# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

#from copilotkit.langgraph import copilotkit_emit_state, copilotkit_customize_config
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

from copilotkit.langgraph import copilotkit_emit_state

from sc_flow.agents.aml_handler.aml_utils import get_document_dataset_name_and_versions
from sc_flow.agents.state import State, AvailableDatasets
from sc_flow.data.model import SelectedDatasets
from sc_flow.utils import llm_generator
from sc_flow.agents.aml_handler import indexer_controller
from langgraph.types import interrupt


graph_indexer_conceirge_prompt = ChatPromptTemplate([
    ("system", """ 
    You are a friendly analyst assistant who will be helping users in submitting a graph indexing job on Azure Machine Learning. 
    Your job is to acknowledge the user's request to submit an indexing job and then search for documents that are available for indexing.
    These documents will be stored in an Azure ML dataset object. A separate process will fetch the datasets. 
    """), 
    ("user", """{context}""")
])

verification_prompt = ChatPromptTemplate([
    ("system", """ 
    You are a friendly analyst assistant who will be helping a user select one or more documents to process. You'll be provided a list of document 
     datasets that exist in Azure ML, and you'll display the names and versions to the user in a very human-readable way. The user will
     then select one or more for further processing. 
     
     Do not engage in any preamble. Simply let the user know that you've found these datasets and ask for their selections:
     
    {list_of_datasets} 
    """), 
    ("user", """{context}""")
])

submission_prompt = ChatPromptTemplate([
    ("system", """ 
    You are a friendly analyst assistant who will be helping a user launch an Azure ML processing job on one or more datasets. You'll be given 
     a list of available datasets along with user selection. From the user selection, identify which datasets from the list of available datasets
     correspond to the user's choices.

     Do not engage in any preamble, simply let the user know that you will start processing the datasets that have been selected.
    {list_of_datasets}
    """), 
    ("user", """{context}""")
])

async def run_graph_indexer(state: AvailableDatasets, config: RunnableConfig):
    """Submits the graph indexer job to Azure Machine Learning"""

    state["logs"].append({
        "message": f"Submitting the graph indexer job to Azure ML",
        "done": False
    })
    await copilotkit_emit_state(config, state)

    llm = llm_generator()
    chain = (
        {
            "list_of_datasets": lambda x: state["datasets"],
            "context": RunnablePassthrough()
        }
        | submission_prompt
        | llm.with_structured_output(SelectedDatasets)
    )
    resp = await chain.ainvoke(state["messages"])
    state["messages"] = AIMessage(content=resp.response) 

    job_ids = []
    for selected_dataset in resp.selected_datasets:
        job_ids += [indexer_controller(selected_dataset.dataset, selected_dataset.version)]
    job_id_str = ",".join(job_ids)
    state["messages"] = AIMessage(content=f"Azure ML processing has begun! The relevant job url(s) is: {job_id_str}.")

    state["logs"].append({
        "message": f"Submitting the graph indexer job to Azure ML",
        "done": True
    })
    await copilotkit_emit_state(config, state)

    return state

    
async def present_datasets(state: AvailableDatasets, config: RunnableConfig) -> AvailableDatasets:
    """Show the available datasets to the user and let the user select which one(s) to process"""

    state["logs"].append({
        "message": f"Searching for Azure ML datasets",
        "done": False
    })
 
    await copilotkit_emit_state(config, state)

    llm = llm_generator()
    chain = (
        {
            "list_of_datasets": lambda x: state["datasets"],
            "context": RunnablePassthrough()
        }
        | verification_prompt
        | llm
    )
    resp = await chain.ainvoke(state["messages"])
    state["messages"] = resp
    return state 

def confirmation(state: AvailableDatasets, config: RunnableConfig) -> AvailableDatasets:
    choice = interrupt("Which dataset(s) would you like to process?")
    print(choice)
    state["messages"] = HumanMessage(content = choice)
    state['last_user_message'] = choice
    return state

def ingest_document(document_name: str, document_version: str):
    """Ingests a document for evaluation"""
    pass

async def get_datasets(state: State, config: RunnableConfig) -> AvailableDatasets:
    state["logs"].append({
        "message": f"Searching for Azure ML datasets",
        "done": False
    })
    await copilotkit_emit_state(config, state)

    """Call to retrieve a list of datasets (files) from Azure Machine Learning"""
    available_datasets = get_document_dataset_name_and_versions()

    state["logs"].append({
        "message": f"Searching for Azure ML datasets",
        "done": True
    })
    await copilotkit_emit_state(config, state)

    return {
        **state,
        "datasets": available_datasets,
        "task": "index_scg"
    }

async def graph_indexer(state: State, config: RunnableConfig):
    llm = llm_generator()
    chain = (
        {
            "context": RunnablePassthrough()
        }
        | graph_indexer_conceirge_prompt
        | llm
    )
    resp = await chain.ainvoke(state["messages"])
    state["last_user_message"] = resp.content
    state['messages'] = resp.content
    return state

def document_ingester(state: State, config: RunnableConfig):
    pass
