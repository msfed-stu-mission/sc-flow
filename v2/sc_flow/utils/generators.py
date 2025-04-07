# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from sc_flow.data import *
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_community.llms import AzureMLOnlineEndpoint
from typing import Union
import getpass
import os

def _set_if_undefined(var_name: str, default: Optional[str] = None):
    """
    Set an environment variable if it is undefined, with an optional default value.

    Args:
        var_name (str): The name of the environment variable to check or set.
        default (Optional[str]): A default value to return if the environment variable is not set.

    Returns:
        str: The value of the environment variable or the default value.
    """
    value = os.getenv(var_name)
    if not value:
        value = default or getpass.getpass(f"Please provide your {var_name}: ")
        os.environ[var_name] = value
    return value

def _populate_model(model: BaseModel):
    """
    Populates a BaseModel instance by assigning values from environment variables or prompts.

    Args:
        model (BaseModel): The model instance to populate.

    Returns:
        BaseModel: The populated model instance.
    """
    for field_name, field_value in model.dict().items():
        if field_value is None:  
            model_value = _set_if_undefined(field_name)
            setattr(model, field_name, model_value)
    return model

def _set_env_vars(model_config: BaseModel, overwrite_env: bool = False):
    """
    Dynamically set environment variables based on the fields of the BaseModel.

    Args:
        model_config (BaseModel): The configuration model for the desired LLM.
        overwrite_env (bool): Whether to overwrite existing environment variables. Defaults to False.

    Returns:
        dict: A dictionary of the environment variables set or retrieved.
    """
    env_vars = {}
    for field_name, field_value in model_config.dict().items():
        env_var_value = os.getenv(field_name)
        if overwrite_env or env_var_value is None:
            os.environ[field_name] = str(field_value)
            env_vars[field_name] = os.environ[field_name]
        else:
            env_vars[field_name] = env_var_value
    return env_vars

def embeddings_generator():
    """Dynamically set the embedding model config"""
    agent_embeddings = _populate_model(AgentEmbeddings.from_env())
    match agent_embeddings.EMBEDDING_PROVIDER:
        case EmbeddingProvider.azure_openai:
            return _embeddings_generator((_populate_model(AzureOpenAIEmbeddingModel.from_env())))
        case _:
            raise ValueError("Invalid model provider, options are: azure_openai | ollama")

def _embeddings_generator(model_config: Union[AzureOpenAIEmbeddingModel]):
    """Generates an embedding instance on the provided configuration

        Args:
            model_config (Union[AzureOpenAIEmbeddingModel, OllamaEmbeddingModel]): the configuration object for the desired embeddings
        
        Returns:
            An instance of the embeddings
    """

    match model_config:
        case AzureOpenAIEmbeddingModel():
            env_vars = _set_env_vars(model_config)
            return AzureOpenAIEmbeddings(
                azure_deployment=model_config.EMBEDDING_DEPLOYMENT_NAME,
                azure_endpoint=model_config.AZURE_OPENAI_ENDPOINT,
                api_key=model_config.AZURE_OPENAI_API_KEY,
                api_version=model_config.OPENAI_API_VERSION,
            )
        case _:
             raise ValueError("Invalid model configuration")

def llm_generator():
    """Dynamically set the model config."""
    agent_model = _populate_model(AgentModel.from_env())

    match agent_model.MODEL_PROVIDER:
        case LLMProvider.azure_openai:
            return _llm_generator((_populate_model(AzureOpenAIModel.from_env())))
        case LLMProvider.azure_ml:
            return _llm_generator((_populate_model(AzureMachineLearningModel.from_env())))
        case LLMProvider.ollama:
            return _llm_generator((_populate_model(OllamaModel.from_env())))
        case _:
            raise ValueError("Invalid model provider, options are: azure_openai | azure_ml | ollama")

def _llm_generator(model_config: Union[AzureOpenAIModel, AzureMachineLearningModel, OllamaModel]):
    """
    Generates an LLM instance based on the provided model configuration.

    Args:
        model_config (Union[AzureOpenAIModel, AzureMachineLearningModel, OllamaModel]): 
            The configuration object for the desired model.

    Returns:
        An instance of the appropriate LLM model.
    """
    match model_config:
        case AzureOpenAIModel():
            env_vars = _set_env_vars(model_config)
            return AzureChatOpenAI(
                azure_deployment=model_config.LLM_DEPLOYMENT_NAME,
                azure_endpoint=model_config.AZURE_OPENAI_ENDPOINT,
                api_key=model_config.AZURE_OPENAI_API_KEY,
                api_version=model_config.OPENAI_API_VERSION,
            )

        case AzureMachineLearningModel():
            env_vars = _set_env_vars(model_config)
            return AzureMLOnlineEndpoint(
                endpoint_url=model_config.AML_ENDPOINT_URL,
                api_key=model_config.AML_ENDPOINT_API_KEY,
                api_type=model_config.AML_ENDPOINT_API_TYPE,
                content_formatter=model_config.CONTENT_FORMATTER,
                model_kwargs=model_config.MODEL_KWARGS or {},
            )

        case OllamaModel():
            raise NotImplementedError("OllamaModel instantiation is not yet implemented.")

        case _:
            raise ValueError("Invalid model configuration provided.")


def neo4j_vector_generator(topChunks: int, topCommunities: int, topOutsideRels: int, topInsideRels: int):
    from sc_flow.utils.cypher_queries import get_retrieval_query

    neo4j_model = _populate_model(Neo4jStore.from_env()) 
    store = Neo4jVector.from_existing_index(
        embeddings_generator(),
        url=neo4j_model.NEO4J_URI,
        username=neo4j_model.NEO4J_USERNAME,
        password=neo4j_model.NEO4J_PASSWORD,
        index_name=neo4j_model.NEO4J_VECTOR_INDEX,
        text_node_property = neo4j_model.NEO4J_TEXT_NODE_PROPERTY,
        retrieval_query = get_retrieval_query(topChunks, topCommunities, topOutsideRels, topInsideRels)
    )
    return store

def azure_ai_search_generator():
    pass