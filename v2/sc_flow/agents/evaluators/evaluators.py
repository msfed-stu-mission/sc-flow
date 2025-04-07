# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from .prompts import *
from sc_flow.agents.state import ExpertAnalysisState, ClassificationDecision, ExpertResponse
from sc_flow.utils import llm_generator, neo4j_vector_generator
from langchain_core.runnables import RunnablePassthrough, RunnableConfig
from copilotkit.langgraph import copilotkit_emit_state
from langchain.chains import RetrievalQA
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
import ast
import os

def get_search_client():
    search_client = SearchClient(os.environ["AI_SEARCH_ENDPOINT"], 
                                 os.environ["AI_SEARCH_INDEX"], 
                                 AzureKeyCredential(os.environ["AI_SEARCH_KEY"]))
    return search_client

async def ts_evaluator(state: ExpertAnalysisState, config: RunnableConfig):
    state["logs"].append({
        "message": f"Top Secret Evaluator agent is analyzing...",
        "done": False
    })
 
    #await copilotkit_emit_state(config, state)

    topChunks = os.environ.get("TOP_CHUNKS", 3)
    topCommunities = os.environ.get("TOP_COMMUNITIES", 3)
    topInsideRels = os.environ.get("TOP_INSIDE_RELS", 10)
    topOutsideRels = os.environ.get("TOP_OUTSIDE_RELS", 10)

    search_client = get_search_client()
    store = neo4j_vector_generator(topChunks, topCommunities, topOutsideRels, topInsideRels)
    llm = llm_generator()

    graph_chain = RetrievalQA.from_chain_type(
        llm, chain_type="stuff", retriever=store.as_retriever()
    )
    
    ctx = await graph_chain.ainvoke({"query":get_ts_details_prompt}, 
                              return_only_outputs=True)
    top_secret_agent_chain = (
        {
            "context": lambda x: ctx['result'],
            "content": RunnablePassthrough()
        }
        | ts_evaluator_prompt
        | llm.with_structured_output(ClassificationDecision)
    )

    positive_decisions = []
    async with search_client:
        results = await search_client.search(search_text=state['ctx_doc'])
        async for result in results:
            metadata = ast.literal_eval(result["metadata"])
            if metadata["doc_name"] != state['ctx_doc']:
                continue
            resp = await top_secret_agent_chain.ainvoke(result["content"])
            if resp["classification"] == "Top Secret":
                positive_decisions += [{**resp, "original_content": result['content']}]

    state['classification_analysis'] += [("top_secret_expert_agent", positive_decisions)]
    state["logs"].append({
        "message": f"Top Secret Evaluator agent is analyzing...",
        "done": True
    })
 
    #await copilotkit_emit_state(config, state)

    return state

async def s_evaluator(state: ExpertAnalysisState, config: RunnableConfig):
    state["logs"].append({
        "message": f"Secret Evaluator agent is analyzing...",
        "done": False
    })
 
    #await copilotkit_emit_state(config, state)

    topChunks = os.environ.get("TOP_CHUNKS", 3)
    topCommunities = os.environ.get("TOP_COMMUNITIES", 3)
    topInsideRels = os.environ.get("TOP_INSIDE_RELS", 10)
    topOutsideRels = os.environ.get("TOP_OUTSIDE_RELS", 10)

    search_client = get_search_client()
    store = neo4j_vector_generator(topChunks, topCommunities, topOutsideRels, topInsideRels)
    llm = llm_generator()

    graph_chain = RetrievalQA.from_chain_type(
        llm, chain_type="stuff", retriever=store.as_retriever()
    )
    
    ctx = await graph_chain.ainvoke({"query":get_s_details_prompt}, 
                              return_only_outputs=True)
    secret_agent_chain = (
        {
            "context": lambda x: ctx['result'],
            "content": RunnablePassthrough()
        }
        | s_evaluator_prompt
        | llm.with_structured_output(ClassificationDecision)
    )

    positive_decisions = []
    async with search_client:
        results = await search_client.search(search_text=state['ctx_doc'])
        async for result in results:
            metadata = ast.literal_eval(result["metadata"])
            if metadata["doc_name"] != state['ctx_doc']:
                continue
            resp = await secret_agent_chain.ainvoke(result["content"])
            if resp["classification"] == "Secret":
                positive_decisions += [{**resp, "original_content": result['content']}]

    state['classification_analysis'] += [("secret_expert_agent", positive_decisions)]
    state["logs"].append({
        "message": f"Secret Evaluator agent is analyzing...",
        "done": True
    })
 
    #await copilotkit_emit_state(config, state)

    return state

async def unclass_evaluator(state: ExpertAnalysisState, config: RunnableConfig):
    state["logs"].append({
        "message": f"Unclass Evaluator agent is analyzing...",
        "done": False
    })
 
    #await copilotkit_emit_state(config, state)

    topChunks = os.environ.get("TOP_CHUNKS", 3)
    topCommunities = os.environ.get("TOP_COMMUNITIES", 3)
    topInsideRels = os.environ.get("TOP_INSIDE_RELS", 10)
    topOutsideRels = os.environ.get("TOP_OUTSIDE_RELS", 10)

    search_client = get_search_client()
    store = neo4j_vector_generator(topChunks, topCommunities, topOutsideRels, topInsideRels)
    llm = llm_generator()

    graph_chain = RetrievalQA.from_chain_type(
        llm, chain_type="stuff", retriever=store.as_retriever()
    )
    
    ctx = await graph_chain.ainvoke({"query":get_unclass_details_prompt}, 
                              return_only_outputs=True)
    unclass_agent_chain = (
        {
            "context": lambda x: ctx['result'],
            "content": RunnablePassthrough()
        }
        | unclass_evaluator_prompt
        | llm.with_structured_output(ClassificationDecision)
    )

    positive_decisions = []
    async with search_client:
        results = await search_client.search(search_text=state['ctx_doc'])
        async for result in results:
            metadata = ast.literal_eval(result["metadata"])
            if metadata["doc_name"] != state['ctx_doc']:
                continue
            resp = await unclass_agent_chain.ainvoke(result["content"])
            if resp["classification"] == "Unclassified" or resp['classification'] == "CUI":
                positive_decisions += [{**resp, "original_content": result['content']}]

    state['classification_analysis'] += [("unclass_expert_agent", positive_decisions)]
    state["logs"].append({
        "message": f"Unclass Evaluator agent is analyzing...",
        "done": True
    })
 
    #await copilotkit_emit_state(config, state)

    return state