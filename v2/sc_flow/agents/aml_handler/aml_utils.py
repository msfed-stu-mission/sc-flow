# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from sc_flow.utils.generators import _set_if_undefined
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
import os

def _verify_aml_vars():
    """Verify AzureML vars exist"""
    _set_if_undefined("AZURE_ENVIRONMENT")
    _set_if_undefined("AML_GRAPH_INDEXER_IMAGE_NAME")
    _set_if_undefined("AML_DOCUMENT_PROCESSOR_IMAGE_NAME")
    _set_if_undefined("AML_WORKSPACE_NAME")
    _set_if_undefined("AML_RESOURCE_GROUP")
    _set_if_undefined("AML_SUBSCRIPTION_ID")
    _set_if_undefined("AML_DOCUMENT_DATASET_NAME")
    _set_if_undefined("AML_SCG_DATASET_NAME")

def authenticate_client() -> MLClient:
    """Connect to the AzureML workspace"""
    ml_client = MLClient(workspace_name=os.getenv("AML_WORKSPACE_NAME"),
                        resource_group_name=os.getenv("AML_RESOURCE_GROUP"),
                        subscription_id=os.getenv("AML_SUBSCRIPTION_ID"),
                        credential = DefaultAzureCredential(), 
                        cloud=os.getenv("AZURE_ENVIRONMENT")) 
    return ml_client 

def get_document_dataset_name_and_versions(dataset_name = None) -> list:
    _verify_aml_vars()
    ml_client = authenticate_client()
    return list((dataset.name, dataset.latest_version if dataset.latest_version is not None else 1) for dataset in ml_client.data.list(dataset_name))

    
