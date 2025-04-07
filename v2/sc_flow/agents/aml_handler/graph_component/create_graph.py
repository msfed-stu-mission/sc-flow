# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

#TODO: maybe break this up into a multi-step AzureML pipeline? 

import os
import logging
from graphdatascience import GraphDataScience
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Neo4jVector
from langchain_experimental.graph_transformers.llm import LLMGraphTransformer
from langchain_core.output_parsers import StrOutputParser
from langchain_community.graphs import Neo4jGraph
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional
import pandas as pd
import numpy as np
import tiktoken
import mlflow
import matplotlib.pyplot as plt
import seaborn as sns
from prompt import *

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def num_tokens_from_string(string: str, model: str = "gpt-4o") -> int:
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def build_degree_dist(graph: Neo4jGraph):
    degree_dist = graph.query(
        """
        MATCH (e:__Entity__)
        RETURN count {(e)-[:!MENTIONS]-()} AS node_degree
        """
    )
    degree_dist_df = pd.DataFrame.from_records(degree_dist)

    mean_degree = np.mean(degree_dist_df["node_degree"])
    percentiles = np.percentile(degree_dist_df["node_degree"], [25, 50, 75, 90])
    fig = plt.figure(figsize=(12, 6))
    sns.histplot(degree_dist_df["node_degree"], bins=50, kde=False, color="blue")
    plt.yscale("log")
    plt.xlabel("Node Degree")
    plt.ylabel("Count (log scale)")
    plt.title("Node Degree Distribution")
    plt.axvline(
        mean_degree,
        color="red",
        linestyle="dashed",
        linewidth=1,
        label=f"Mean: {mean_degree:.2f}",
    )
    plt.axvline(
        percentiles[0],
        color="purple",
        linestyle="dashed",
        linewidth=1,
        label=f"25th Percentile: {percentiles[0]:.2f}",
    )
    plt.axvline(
        percentiles[1],
        color="orange",
        linestyle="dashed",
        linewidth=1,
        label=f"50th Percentile: {percentiles[1]:.2f}",
    )
    plt.axvline(
        percentiles[2],
        color="yellow",
        linestyle="dashed",
        linewidth=1,
        label=f"75th Percentile: {percentiles[2]:.2f}",
    )
    plt.axvline(
        percentiles[3],
        color="brown",
        linestyle="dashed",
        linewidth=1,
        label=f"90th Percentile: {percentiles[3]:.2f}",
    )
    plt.legend()

    mlflow.log_figure(fig, "Node_Degree_Distribution.png")


def build_entity_dist(graph: Neo4jGraph):
    entity_dist = graph.query(
        """
        MATCH (d:Document)
        RETURN d.text AS text,
            count {(d)-[:MENTIONS]->()} AS entity_count
        """
    )
    entity_dist_df = pd.DataFrame.from_records(entity_dist)
    entity_dist_df["token_count"] = [
        num_tokens_from_string(str(el)) for el in entity_dist_df["text"]
    ]
    plot = sns.lmplot(
        x="token_count",
        y="entity_count",
        data=entity_dist_df,
        line_kws={"color": "red"},
    )
    plt.title("Entity Count vs Token Count Distribution")
    plt.xlabel("Token Count")
    plt.ylabel("Entity Count")

    mlflow.log_figure(plot.fig, "Entity_Distribution.png")


def augment_similarities(gds: GraphDataScience):
    G, result = gds.graph.project(
        "entities", "__Entity__", "*", nodeProperties=["embedding"]
    )
    gds.knn.mutate(
        G,
        nodeProperties=["embedding"],
        mutateRelationshipType="SIMILAR",
        mutateProperty="score",
        similarityCutoff=0.95,
    )
    gds.wcc.write(G, writeProperty="wcc", relationshipTypes=["SIMILAR"])


class DuplicateEntities(BaseModel):
    entities: List[str] = Field(
        description="Entities that represent the same object or real-world entity and should be merged"
    )


class Disambiguate(BaseModel):
    merge_entities: Optional[List[DuplicateEntities]] = Field(
        description="Lists of entities that represent the same object or real-world entity and should be merged"
    )


def augment_dedup(gds: GraphDataScience, graph: Neo4jGraph, llm: AzureChatOpenAI):
    word_edit_distance = 3
    potential_duplicate_candidates = graph.query(
        """MATCH (e:`__Entity__`)
        WHERE size(e.id) > 4 // longer than 4 characters
        WITH e.wcc AS community, collect(e) AS nodes, count(*) AS count
        WHERE count > 1
        UNWIND nodes AS node
        // Add text distance
        WITH distinct
        [n IN nodes WHERE apoc.text.distance(toLower(node.id), toLower(n.id)) < $distance | n.id] AS intermediate_results
        WHERE size(intermediate_results) > 1
        WITH collect(intermediate_results) AS results
        // combine groups together if they share elements
        UNWIND range(0, size(results)-1, 1) as index
        WITH results, index, results[index] as result
        WITH apoc.coll.sort(reduce(acc = result, index2 IN range(0, size(results)-1, 1) |
                CASE WHEN index <> index2 AND
                    size(apoc.coll.intersection(acc, results[index2])) > 0
                    THEN apoc.coll.union(acc, results[index2])
                    ELSE acc
                END
        )) as combinedResult
        WITH distinct(combinedResult) as combinedResult
        // extra filtering
        WITH collect(combinedResult) as allCombinedResults
        UNWIND range(0, size(allCombinedResults)-1, 1) as combinedResultIndex
        WITH allCombinedResults[combinedResultIndex] as combinedResult, combinedResultIndex, allCombinedResults
        WHERE NOT any(x IN range(0,size(allCombinedResults)-1,1)
            WHERE x <> combinedResultIndex
            AND apoc.coll.containsAll(allCombinedResults[x], combinedResult)
        )
        RETURN combinedResult
        """,
        params={"distance": word_edit_distance},
    )

    extraction_llm = llm.with_structured_output(Disambiguate)
    extraction_chain = extraction_prompt | extraction_llm

    def entity_resolution(entities: List[str]) -> Optional[List[str]]:
        return [
            el.entities
            for el in extraction_chain.invoke({"entities": entities}).merge_entities
        ]

    merged_entities = []
    for el in potential_duplicate_candidates:
        merged_entities.extend(entity_resolution(el["combinedResult"]))

    graph.query(
        """
        UNWIND $data AS candidates
        CALL {
        WITH candidates
        MATCH (e:__Entity__) WHERE e.id IN candidates
        RETURN collect(e) AS nodes
        }
        CALL apoc.refactor.mergeNodes(nodes, {properties: {
            `.*`: 'discard'
        }})
        YIELD node
        RETURN count(*)
        """,
        params={"data": merged_entities},
    )


def augment_summarize(gds: GraphDataScience, graph: Neo4jGraph, llm: AzureChatOpenAI):
    G, result = gds.graph.project(
        "communities",
        "__Entity__",
        {
            "_ALL_": {
                "type": "*",
                "orientation": "UNDIRECTED",
                "properties": {"weight": {"property": "*", "aggregation": "COUNT"}},
            }
        },
    )

    wcc = gds.wcc.stats(G)
    mlflow.log_metric("WCC Component Count", wcc["componentCount"])

    gds.leiden.write(
        G,
        writeProperty="communities",
        includeIntermediateCommunities=True,
        relationshipWeightProperty="weight",
    )
    graph.query(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:__Community__) REQUIRE c.id IS UNIQUE;"
    )

    graph.query(
        """
        MATCH (e:`__Entity__`)
        UNWIND range(0, size(e.communities) - 1 , 1) AS index
        CALL {
        WITH e, index
        WITH e, index
        WHERE index = 0
        MERGE (c:`__Community__` {id: toString(index) + '-' + toString(e.communities[index])})
        ON CREATE SET c.level = index
        MERGE (e)-[:IN_COMMUNITY]->(c)
        RETURN count(*) AS count_0
        }
        CALL {
        WITH e, index
        WITH e, index
        WHERE index > 0
        MERGE (current:`__Community__` {id: toString(index) + '-' + toString(e.communities[index])})
        ON CREATE SET current.level = index
        MERGE (previous:`__Community__` {id: toString(index - 1) + '-' + toString(e.communities[index - 1])})
        ON CREATE SET previous.level = index - 1
        MERGE (previous)-[:IN_COMMUNITY]->(current)
        RETURN count(*) AS count_1
        }
        RETURN count(*)
        """
    )

    graph.query(
        """
        MATCH (c:__Community__)<-[:IN_COMMUNITY*]-(:__Entity__)<-[:MENTIONS]-(d:Document)
        WITH c, count(distinct d) AS rank
        SET c.community_rank = rank;
        """
    )

    community_size = graph.query(
        """
    MATCH (c:__Community__)<-[:IN_COMMUNITY*]-(e:__Entity__)
    WITH c, count(distinct e) AS entities
    RETURN split(c.id, '-')[0] AS level, entities
    """
    )
    community_size_df = pd.DataFrame.from_records(community_size)
    percentiles_data = []
    for level in community_size_df["level"].unique():
        subset = community_size_df[community_size_df["level"] == level]["entities"]
        num_communities = len(subset)
        percentiles = np.percentile(subset, [25, 50, 75, 90, 99])
        percentiles_data.append(
            [
                level,
                num_communities,
                percentiles[0],
                percentiles[1],
                percentiles[2],
                percentiles[3],
                percentiles[4],
                max(subset),
            ]
        )

    percentiles_df = pd.DataFrame(
        percentiles_data,
        columns=[
            "Level",
            "Number of communities",
            "25th Percentile",
            "50th Percentile",
            "75th Percentile",
            "90th Percentile",
            "99th Percentile",
            "Max",
        ],
    )
    percentile_columns = [
        "25th Percentile",
        "50th Percentile",
        "75th Percentile",
        "90th Percentile",
        "99th Percentile",
        "Max",
    ]
    data_for_histogram = percentiles_df[percentile_columns].values.flatten()

    fig = plt.figure(figsize=(10, 6))
    plt.hist(data_for_histogram, bins=10, color="skyblue", edgecolor="black")
    plt.title("Distribution of Percentile Values")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    mlflow.log_figure(fig, "Community_Percentiles.png")

    community_info = graph.query(
        """
        MATCH (c:`__Community__`)<-[:IN_COMMUNITY*]-(e:__Entity__)
        WHERE c.level IN [0,1,4]
        WITH c, collect(e ) AS nodes
        WHERE size(nodes) > 1
        CALL apoc.path.subgraphAll(nodes[0], {
            whitelistNodes:nodes
        })
        YIELD relationships
        RETURN c.id AS communityId,
            [n in nodes | {id: n.id, description: n.description, type: [el in labels(n) WHERE el <> '__Entity__'][0]}] AS nodes,
            [r in relationships | {start: startNode(r).id, type: type(r), end: endNode(r).id, description: r.description}] AS rels
        """
    )

    community_chain = community_prompt | llm | StrOutputParser()

    def prepare_string(data):
        nodes_str = "Nodes are:\n"
        for node in data["nodes"]:
            node_id = node["id"]
            node_type = node["type"]
            if "description" in node and node["description"]:
                node_description = f", description: {node['description']}"
            else:
                node_description = ""
            nodes_str += f"id: {node_id}, type: {node_type}{node_description}\n"

        rels_str = "Relationships are:\n"
        for rel in data["rels"]:
            start = rel["start"]
            end = rel["end"]
            rel_type = rel["type"]
            if "description" in rel and rel["description"]:
                description = f", description: {rel['description']}"
            else:
                description = ""
            rels_str += f"({start})-[:{rel_type}]->({end}){description}\n"
        return nodes_str + "\n" + rels_str

    def process_community(community):
        stringify_info = prepare_string(community)
        summary = community_chain.invoke({"community_info": stringify_info})
        return {"community": community["communityId"], "summary": summary}

    summaries = []
    for community in community_info:
        summaries.append(process_community(community))

    graph.query(
        """
        UNWIND $data AS row
        MERGE (c:__Community__ {id:row.community})
        SET c.summary = row.summary
        """,
        params={"data": summaries},
    )


def create_graph(scg_dataset: str) -> str:
    with mlflow.start_run():
        logger.info("Updating the SCG Knowledge Graph.")

        graph = Neo4jGraph(
            url=os.environ["NEO4J_URI"],
            username=os.environ["NEO4J_USERNAME"],
            password=os.environ["NEO4J_PASSWORD"],
            database=os.environ.get("NEO4J_DATABASE", "neo4j"),
        )

        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.environ["EMBEDDING_DEPLOYMENT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )

        llm = AzureChatOpenAI(
            azure_deployment=os.environ["MODEL_DEPLOYMENT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )

        semantic_splitter = SemanticChunker(
            embeddings, breakpoint_threshold_type="percentile"
        )

        transformer = LLMGraphTransformer(
            llm=llm,
            relationship_properties=True,
            node_properties=True,
            prompt=graph_prompt,
        )

        logger.info("Semantically chunking the guide... (this might take a while)")
        docs = PyPDFLoader(scg_dataset).load_and_split(semantic_splitter)

        logger.info("Creating the graph structure... (this will take a while)")
        graph_struct = transformer.convert_to_graph_documents(docs)

        logger.info("Inserting into the graph store...")
        graph.add_graph_documents(
            graph_struct,
            baseEntityLabel=True,
            include_source=True
        )

        logger.info("Saving artifacts...")
        build_degree_dist(graph)
        build_entity_dist(graph)

        logger.info("Calculating node embeddings...")
        vector = Neo4jVector.from_existing_graph(
            embeddings,
            node_label="__Entity__",
            text_node_properties=["id", "description"],
            embedding_node_property="embedding",
        )

        logger.info("Augmenting graph...")
        gds = GraphDataScience(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
        augment_similarities(gds)
        augment_dedup(gds, graph, llm)
        augment_summarize(gds, graph, llm)

        logger.info("Validating vector index...")
        graph.query(
            """
            CREATE VECTOR INDEX entity
            IF NOT EXISTS FOR (e:__Entity__) ON e.embedding
            OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
            }}
            """
        )

        logger.info("Setting community weights...")
        graph.query("""
            MATCH (n:`__Community__`)<-[:IN_COMMUNITY]-()<-[]-(c:`__Entity__`)
            WITH n, count(distinct c) AS chunkCount
            SET n.weight = chunkCount
        """)
        logger.info("Done.")
