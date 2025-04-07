# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from .state import State
from .user_proxy.agent import user_proxy
from .scg_handler.agent import scg_analyst
from .evaluators.orchestrator import agent_scatter, classifier_orchestrator
from .evaluators.evaluators import s_evaluator, ts_evaluator, unclass_evaluator
from .classifier_authority.agent import classifier_authority
from .document_processors.agent import graph_indexer, document_ingester, get_datasets, confirmation, run_graph_indexer, present_datasets
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

global graph
graph = None

def get_or_build_graph(reinitialize: bool = False, saver = None):
    if graph and not reinitialize:
        return graph
    return _build_graph(saver)

def get_graph_builder():
    return _build_workflow()

def _build_workflow():
    """Build the agent workflow but don't compile yet"""
    graph_builder = StateGraph(State)
    graph_builder.add_node("user_proxy", user_proxy)
    graph_builder.add_node("scg_analyst", scg_analyst)
    graph_builder.add_node("classifier_orchestrator",classifier_orchestrator)

    graph_builder.add_node("start_processor_request", document_ingester)
    graph_builder.add_node("start_indexer_request", graph_indexer)
    graph_builder.add_node("fetch_available_documents", get_datasets)
    graph_builder.add_node("fetch_available_scgs", get_datasets)
    graph_builder.add_node("present_available_data", present_datasets)
    graph_builder.add_node("confirm_with_user", confirmation)

    graph_builder.add_node("submit_indexer", run_graph_indexer)
    graph_builder.add_node("submit_processor", run_graph_indexer)

    graph_builder.add_node("unclass_evaluator", unclass_evaluator)
    graph_builder.add_node("s_evaluator", s_evaluator)
    graph_builder.add_node("ts_evaluator", ts_evaluator)
    graph_builder.add_node("classifier_authority", classifier_authority)

    graph_builder.add_edge(START, "user_proxy")
    graph_builder.add_conditional_edges(
        "user_proxy", 
        lambda state: state["next_agent"], 
        {
            "security_classification_guide_expert": "scg_analyst",
            "document_classification_experts": "classifier_orchestrator",
            "security_classification_guide_indexer": "start_indexer_request",
            "document_indexer": "start_processor_request",
            "default": END,
            "user_proxy": END
        }
    )

    graph_builder.add_conditional_edges("classifier_orchestrator", 
                                    agent_scatter, 
                                    ["ts_evaluator", "s_evaluator", "unclass_evaluator"],
                                    then="classifier_authority")

    graph_builder.add_edge("start_indexer_request", "fetch_available_scgs")
    graph_builder.add_edge("start_processor_request", "fetch_available_documents")
    graph_builder.add_edge("fetch_available_scgs", "present_available_data")
    graph_builder.add_edge("fetch_available_documents", "present_available_data")

    graph_builder.add_edge("present_available_data", "confirm_with_user")

    graph_builder.add_conditional_edges(
        "confirm_with_user",
        lambda state: state['task'],
        {
            "index_scg": "submit_indexer",
            "ingest_document": "submit_processor",
        }               
    )

    graph_builder.add_edge("submit_indexer", END)
    graph_builder.add_edge("submit_processor", END)
    graph_builder.add_edge("scg_analyst", END)
    graph_builder.add_edge("classifier_authority", END)
    return graph_builder

def _build_graph(saver = None):
    """Build the agent graph"""
    workflow = _build_workflow()
    if not saver:
        saver = MemorySaver()
    graph = workflow.compile(checkpointer=saver)
    return graph