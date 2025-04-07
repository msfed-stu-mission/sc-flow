# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from langchain_community.llms.azureml_endpoint import (
    AzureMLEndpointApiType,
    CustomOpenAIContentFormatter
)
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import os

class LLMProvider(str, Enum):
    """Available LLM providers"""
    azure_openai: str = "azure_openai"
    ollama: str = "ollama"
    azure_ml: str = "azure_ml" 

class EmbeddingProvider(str, Enum):
    """Available embedding providers"""
    azure_openai: str = "azure_openai"
    ollama: str = "ollama"

class AgentEmbeddings(BaseModel):
    EMBEDDING_PROVIDER: Optional[EmbeddingProvider]

    @classmethod
    def from_env(cls):
        """Load embedding provider from environment variable."""
        return cls(EMBEDDING_PROVIDER=os.getenv("EMBEDDING_PROVIDER", EmbeddingProvider.azure_openai))

class AgentModel(BaseModel):
    MODEL_PROVIDER: Optional[LLMProvider]

    @classmethod
    def from_env(cls):
        """Load model provider from environment variable."""
        return cls(MODEL_PROVIDER=os.getenv("MODEL_PROVIDER", LLMProvider.azure_openai))

class AzureOpenAIModel(BaseModel):
    OPENAI_API_VERSION: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    LLM_DEPLOYMENT_NAME: str | None = None

    @classmethod
    def from_env(cls):
        """Create model instance with values from environment variables."""
        return cls(
            OPENAI_API_VERSION=os.getenv("OPENAI_API_VERSION"),
            AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT"),
            AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY"),
            DEPLOYMENT_NAME=os.getenv("LLM_DEPLOYMENT_NAME"),
        )

    class Config:
        arbitrary_types_allowed = True

class AzureMachineLearningModel(BaseModel):
    AML_ENDPOINT_URL: str | None = None
    AML_ENDPOINT_API_TYPE: AzureMLEndpointApiType = AzureMLEndpointApiType.dedicated
    AML_ENDPOINT_API_KEY: str | None = None
    CONTENT_FORMATTER: CustomOpenAIContentFormatter = CustomOpenAIContentFormatter()
    MODEL_KWARGS: Optional[dict] = None

    @classmethod
    def from_env(cls):
        """Create model instance with values from environment variables."""
        return cls(
            AML_ENDPOINT_URL=os.getenv("AML_ENDPOINT_URL"),
            AML_ENDPOINT_API_TYPE=AzureMLEndpointApiType.dedicated,
            AML_ENDPOINT_API_KEY=os.getenv("AML_ENDPOINT_API_KEY"),
            CONTENT_FORMATTER=CustomOpenAIContentFormatter(),
            MODEL_KWARGS=None,
        )

    class Config:
        arbitrary_types_allowed = True

class OllamaModel(BaseModel):
    @classmethod
    def from_env(cls):
        """Create model instance with values from environment variables."""
        # TODO: implement
        return cls()

    class Config:
        arbitrary_types_allowed = True

class AzureOpenAIEmbeddingModel(BaseModel):
    OPENAI_API_VERSION: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    EMBEDDING_DEPLOYMENT_NAME: str | None = None

    @classmethod
    def from_env(cls):
        """Create model instance with values from environment variables."""
        return cls(
            OPENAI_API_VERSION=os.getenv("OPENAI_API_VERSION"),
            AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT"),
            AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY"),
            DEPLOYMENT_NAME=os.getenv("EMBEDDING_DEPLOYMENT_NAME"),
        )

    class Config:
        arbitrary_types_allowed = True

class Neo4jStore(BaseModel):
    NEO4J_URI: str | None = None
    NEO4J_USERNAME: str | None = None
    NEO4J_PASSWORD: str | None = None
    NEO4J_DATABASE: str | None = None
    NEO4J_VECTOR_INDEX: str | None = None
    NEO4J_TEXT_NODE_PROPERTY: str | None = None 

    @classmethod
    def from_env(cls):
        """Create store instance with values from environment variables."""
        return cls(
            NEO4J_URI=os.getenv("NEO4J_URI"),
            NEO4J_USERNAME=os.getenv("NEO4J_USERNAME"),
            NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD"),
            NEO4J_DATABASE=os.getenv("NEO4J_DATABASE"),
            NEO4J_VECTOR_INDEX=os.getenv("NEO4J_VECTOR_INDEX"),
            NEO4J_TEXT_NODE_PROPERTY=os.getenv("NEO4J_TEXT_NODE_PROPERTY")
        )

    class Config:
        arbitrary_types_allowed = True

class SelectedDataset(BaseModel):
    dataset: str
    version: str

class SelectedDatasets(BaseModel):
    response: str
    selected_datasets: List[SelectedDataset]
