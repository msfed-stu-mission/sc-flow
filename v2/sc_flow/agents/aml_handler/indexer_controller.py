# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import List
from sc_flow.agents.aml_handler.aml_utils import _verify_aml_vars
from sc_flow.utils.generators import _set_if_undefined
from azure.identity import DefaultAzureCredential
from azure.ai.ml.constants import AssetTypes, InputOutputModes
from azure.ai.ml import MLClient, Input, load_component
from azure.ai.ml.dsl import pipeline
import os

def get_var_dict():
    _verify_aml_vars()
    _set_if_undefined("AZURE_OPENAI_API_KEY")
    _set_if_undefined("AZURE_OPENAI_ENDPOINT")
    _set_if_undefined("OPENAI_API_VERSION")
    _set_if_undefined("LLM_DEPLOYMENT_NAME")
    _set_if_undefined("EMBEDDING_DEPLOYMENT_NAME")
    _set_if_undefined("NEO4J_URI")
    _set_if_undefined("NEO4J_USERNAME")
    _set_if_undefined("NEO4J_PASSWORD")
    _set_if_undefined("NEO4J_DATABASE")
    _set_if_undefined("NLM_INGESTOR_ENDPOINT")
    _set_if_undefined("AI_SEARCH_ENDPOINT")
    _set_if_undefined("AI_SEARCH_KEY")
    _set_if_undefined("AI_SEARCH_INDEX")
    _set_if_undefined("NLM_INGESTOR_ENDPOINT")


    env_vars = {
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_VERSION": os.getenv("OPENAI_API_VERSION"),
        "MODEL_DEPLOYMENT": os.getenv("LLM_DEPLOYMENT_NAME"),
        "EMBEDDING_DEPLOYMENT": os.getenv("EMBEDDING_DEPLOYMENT_NAME"),

        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),

        "AML_WORKSPACE_NAME": os.getenv("AML_WORKSPACE_NAME"),
        "AML_RESOURCE_GROUP": os.getenv("AML_RESOURCE_GROUP"),
        "AML_SUBSCRIPTION_ID": os.getenv("AML_SUBSCRIPTION_ID"),
        "NLM_INGESTOR_ENDPOINT": os.getenv("NLM_INGESTOR_ENDPOINT"),
        "AI_SEARCH_ENDPOINT": os.getenv("AI_SEARCH_ENDPOINT"),
        "AI_SEARCH_KEY": os.getenv("AI_SEARCH_KEY"),
        "AI_SEARCH_INDEX": os.getenv("AI_SEARCH_INDEX"),
        "NLM_INGESTOR_ENDPOINT": os.getenv("NLM_INGESTOR_ENDPOINT"),
    }
    return env_vars

def document_processor_controller(doc_sas_url: str | List[str]):
    env_vars = get_var_dict()
    env_vars["DOCUMENT_SAS_URLS"] = str(doc_sas_url)

    ml_client = MLClient(workspace_name=os.getenv("AML_WORKSPACE_NAME"),
                        resource_group_name=os.getenv("AML_RESOURCE_GROUP"),
                        subscription_id=os.getenv("AML_SUBSCRIPTION_ID"),
                        credential = DefaultAzureCredential(), 
                        cloud=os.getenv("AZURE_ENVIRONMENT"))
    
    processor_component = load_component(source="./sc_flow/agents/aml_handler/processor_component/create_doc_processor_component.yaml")
    processor_component.environment.image = os.getenv("AML_DOCUMENT_PROCESSOR_IMAGE_NAME")

    @pipeline(
        default_compute=os.environ.get("AML_COMPUTE_NAME", "default-compute"),
    )
    def ingest_and_process_document():
        graph_node = processor_component()
        graph_node.environment_variables = env_vars

    pipeline_job = ingest_and_process_document()
    pipeline_job = ml_client.jobs.create_or_update(
        pipeline_job, experiment_name="scflow_ingest_and_process_doc"
    )
    return pipeline_job.studio_url

def indexer_controller(scg_dataset: str, dataset_version: str):
    env_vars = get_var_dict()

    ml_client = MLClient(workspace_name=os.getenv("AML_WORKSPACE_NAME"),
                        resource_group_name=os.getenv("AML_RESOURCE_GROUP"),
                        subscription_id=os.getenv("AML_SUBSCRIPTION_ID"),
                        credential = DefaultAzureCredential(), #TODO: service principal
                        cloud=os.getenv("AZURE_ENVIRONMENT")) 

    graph_component = load_component(source="./sc_flow/agents/aml_handler/graph_component/create_graph_component.yaml")
    graph_component.environment.image = os.getenv("AML_GRAPH_INDEXER_IMAGE_NAME")

    scg_input = Input(path=f"azureml:{scg_dataset}:{dataset_version}", 
                      type=AssetTypes.URI_FILE, 
                      mode=InputOutputModes.RO_MOUNT)

    @pipeline(
        default_compute=os.environ.get("AML_COMPUTE_NAME", "default-compute"),
    )
    def create_scg_graph(pipeline_input_data):
        graph_node = graph_component(scg_dataset=pipeline_input_data)
        graph_node.environment_variables = env_vars

    pipeline_job = create_scg_graph(pipeline_input_data=scg_input)
    pipeline_job = ml_client.jobs.create_or_update(
        pipeline_job, experiment_name="scflow_create_scg_knowledge_graph"
    )
    return pipeline_job.studio_url