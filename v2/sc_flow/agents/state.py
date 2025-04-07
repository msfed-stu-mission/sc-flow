# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Literal, List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from copilotkit import CopilotKitState
import operator

class Log(TypedDict):
    """Represents a log of an action performed by the agent"""
    message: str
    done: bool

class State(CopilotKitState):
    """State of the user-facing agent"""
    last_user_message: Annotated[str, lambda x,y: y]
    next_agent: Annotated[str, lambda x,y: y]
    ctx_doc: str
    logs: Annotated[list, operator.add]

class Router(TypedDict):
    """
    Inner data model for agent routing
    """
    response: str
    next_agent: str
    selected_document_name: Optional[str]

class AvailableDatasets(State):
    """Available AzureML datasets"""
    datasets: List
    task: Literal["index_scg", "index_document"]

class ProcessDocument(TypedDict):
    """Process a document"""
    task: Literal["index_scg", "index_document"]
    dataset_name: str
    dataset_version: str
    documents: Optional[List] |  None = None

class ClassificationDecision(TypedDict):
    """Security classification decision with explanation"""
    classification: Literal["Top Secret", "Secret", "CUI", "Unclassified"]
    explanation: str

class ExpertResponse(TypedDict):
    original_content: str

class ExpertAnalysisState(TypedDict):
    """Classification analysis state"""
    #inner_state: Annotated[State, lambda x,y: y]
    #user_query: Annotated[str, lambda x,y: y]
    classification_analysis: Annotated[List[ExpertResponse], operator.add]
    ctx_doc: str
    logs: Annotated[list, operator.add]
    
    class Config:
        arbitrary_types_allowed = True