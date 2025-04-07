# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from sc_flow.agents.state import State, ExpertAnalysisState 
from langgraph.types import Send

def classifier_orchestrator(state: State):
    return {**state, "classification_analysis": []}

def agent_scatter(state: ExpertAnalysisState):
    return [Send(classifier, state) 
            for classifier in ["ts_evaluator", "s_evaluator", "unclass_evaluator"]]
