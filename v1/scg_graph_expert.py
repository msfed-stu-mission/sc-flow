from promptflow import tool
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from promptflow.connections import CustomConnection, AzureOpenAIConnection
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA

topChunks = "3"
topCommunities = "3"
topOutsideRels = "10"
topInsideRels = "10"
topEntities = "10"

retrieval_query = """
WITH collect(node) as nodes
// Entity - Text Unit Mapping
WITH
collect {
    UNWIND nodes as n
    MATCH (n)<-[]->(c:Document)
    WITH c, count(distinct n) as freq
    RETURN c.text AS chunkText
    ORDER BY freq DESC
    LIMIT """ +topChunks+ """
} AS text_mapping,
// Entity - Report Mapping
collect {
    UNWIND nodes as n
    MATCH (n)-[:IN_COMMUNITY]->(c:__Community__)
    WITH c, c.community_rank as rank, c.weight AS weight
    WHERE c.summary is not null
    RETURN c.summary 
    ORDER BY rank, weight DESC
    LIMIT """ +topCommunities+ """
} AS report_mapping,
// Outside Relationships 
collect {
    UNWIND nodes as n
    MATCH (n)-[r]-(m) 
    WHERE NOT m IN nodes
    RETURN type(r) AS descriptionText
    LIMIT """ +topOutsideRels+ """
} as outsideRels,
// Inside Relationships 
collect {
    UNWIND nodes as n
    MATCH (n)-[r]-(m) 
    WHERE m IN nodes
    RETURN type(r) AS descriptionText
    LIMIT """ +topInsideRels+ """
} as insideRels,
// Entities description
collect {
    UNWIND nodes as n
    RETURN n.id AS descriptionText
} as entities
// We don't have covariates or claims here
RETURN {Chunks: text_mapping, Reports: report_mapping, 
       Relationships: outsideRels + insideRels, 
       Entities: entities} AS text, 1.0 AS score, {} AS metadata
"""

@tool
def query_graph(ts_query: str, 
                s_query: str,
                unclass_query: str,
                neo4j_conn: CustomConnection,
                aoai_conn: AzureOpenAIConnection) -> str:

    graph = Neo4jGraph(
        url=neo4j_conn.neo4j_uri,
        username=neo4j_conn.neo4j_username,
        password=neo4j_conn.neo4j_password,
        database=neo4j_conn.neo4j_database,
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-ada-002",
        api_version=aoai_conn.api_version,
        api_key=aoai_conn.api_key,
        azure_endpoint=aoai_conn.api_base,
    )

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o",
        api_version=aoai_conn.api_version,
        api_key=aoai_conn.api_key,
        azure_endpoint=aoai_conn.api_base,
    )

    store = Neo4jVector.from_existing_index(
        embeddings,
        url=neo4j_conn.neo4j_uri,
        username=neo4j_conn.neo4j_username,
        password=neo4j_conn.neo4j_password,
        index_name="vector",
        text_node_property = "description",
        retrieval_query = retrieval_query
    )

    chain = RetrievalQA.from_chain_type(
        llm, chain_type="stuff", retriever=store.as_retriever()
    )


    u_resp = chain.invoke(
        {"query": unclass_query},
        return_only_outputs=True,
    )

    s_resp = chain.invoke(
        {"query": s_query},
        return_only_outputs=True,
    )

    ts_resp = chain.invoke(
        {"query": ts_query},
        return_only_outputs=True,
    )
    
    return {
        "unclassified": u_resp,
        "secret": s_resp,
        "top_secret": ts_resp
    }