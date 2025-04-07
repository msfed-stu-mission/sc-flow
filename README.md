# SC-Flow

SC-Flow is an LLM application designed to facilitate security classification workflows for documents. It integrates with various services, including Azure OpenAI, MongoDB, and Neo4j, to provide a comprehensive solution for document classification.

## Features

- **Agent Workflow**: Implements a graph-based workflow for processing and classifying documents.
- **Optional FastAPI Integration**: Provides RESTful endpoints for interacting with the application.
- **Azure OpenAI Integration**: Leverages Azure OpenAI for embeddings and language model capabilities.
- **MongoDB Checkpointing**: Uses CosmosDB for MongoDB for state persistence.
- **Neo4j GraphRAG**: Supports graph-based document structures using Neo4j.
- **Local and Server Modes**: Can run locally or as a server with configurable endpoints.
- **Promptflow Alternative**: A variation of the system using Promptflow, designed to run in Azure ML.

## Project Structure

- **SC-Flow v1**: a promptflow-based implementation designed to run in Azure Machine Learning. This version is stable and no longer in development.
- **SC-Flow v2**: a langgraph + FastAPI implementation with additional agents, deep integration into Azure Machine Learning, and the ability to upload documents for indexing. This version is in **active development**.
- **SC-Flow Copilot**: the frontend UI for SC-Flow based on CopilotKit. This is in **active development** and may not be fully functional.

  ## Dependencies

  - **SC-Flow v1** is dependent on a promptflow runtime and the following connections:
    - Azure OpenAI 
    - Azure ML (workspace_name, resource_group, subscription_id)
    - Neo4j (neo4j_uri, neo4j_username, neo4j_database, neo4j_password)
      
  - **SC-Flow v2** is dependent on several environment variables detailed in the next section. This application runs in both local and server modes. Local mode is mostly stable, whereas server mode will be dependent on the SC-Flow Copilot UI to function properly. 

# Environment Variables for SC-Flow v2

The v2 requires several environment variables to be configured for proper operation. Below is a detailed description of each variable and its purpose.

## General Configuration

- **`AZURE_ENVIRONMENT`**: Specifies the Azure environment to use. For example, `"AzureUSGovernment"` for government cloud environments.
- **`APPLICATION_HOST`**: The base URL for the application. Default: `"http://localhost:8000"`.
- **`SERVER_ENDPOINT_URL`**: The endpoint URL for the SC-Flow server. Default: `"http://localhost:8000/scflow"`.

## Azure OpenAI Configuration

- **`OPENAI_API_VERSION`**: The API version for Azure OpenAI. Example: `"2024-02-01"`.
- **`AZURE_OPENAI_ENDPOINT`**: The endpoint URL for Azure OpenAI.
- **`AZURE_OPENAI_API_KEY`**: The API key for authenticating with Azure OpenAI.
- **`LLM_DEPLOYMENT_NAME`**: The name of the language model deployment. Example: `"gpt-4o-mini"`.
- **`EMBEDDING_DEPLOYMENT_NAME`**: The name of the embedding model deployment. Example: `"text-embedding-ada-002"`.

## Azure Authentication

- **`AZURE_CLIENT_ID`**: The client ID for Azure authentication.
- **`AZURE_TENANT_ID`**: The tenant ID for Azure authentication.
- **`AZURE_CLIENT_SECRET`**: The client secret for Azure authentication.

## Document Cache Configuration

- **`DOCUMENT_CACHE_URI`**: The URI for the document cache. Example: `"https://<somestoragename>.blob.core.usgovcloudapi.net"`.
- **`DOCUMENT_CACHE_KEY`**: The access key for the document cache.
- **`DOCUMENT_CACHE_CONTAINER`**: The name of the container in the document cache.
- **`DOCUMENT_CACHE_FOLDER`**: The folder path for storing documents. Example: `"uploads"`.
- **`DOCUMENT_CACHE_FOLDER_MODE`**: The folder mode for document storage. Example: `"flat"`.

## NLM Ingestor Configuration

- **`NLM_INGESTOR_ENDPOINT`**: The endpoint for the NLM ingestor service, if using the document indexer.

## AI Search Configuration

- **`AI_SEARCH_ENDPOINT`**: The endpoint for the AI search service.
- **`AI_SEARCH_KEY`**: The API key for the AI search service.
- **`AI_SEARCH_INDEX`**: The name of the search index.

## MongoDB Configuration

- **`MONGODB_USER`**: The username for MongoDB authentication.
- **`MONGODB_PASSWORD`**: The password for MongoDB authentication.
- **`MONGODB_HOST`**: The host address for MongoDB. Example: `"copilot-memory.mongo.cosmos.azure.us"`.
- **`MONGODB_PORT`**: The port for MongoDB. Example: `"10255"`.
- **`MONGODB_DATABASE`**: The name of the MongoDB database. Example: `"copilot-memory"`.

## Neo4j Configuration

- **`NEO4J_URI`**: The bolt URI for the Neo4j database.
- **`NEO4J_USERNAME`**: The username for Neo4j authentication.
- **`NEO4J_PASSWORD`**: The password for Neo4j authentication.
- **`NEO4J_DATABASE`**: The name of the Neo4j database. 
- **`NEO4J_VECTOR_INDEX`**: The name of the vector index in Neo4j.
- **`NEO4J_TEXT_NODE_PROPERTY`**: The property name for text nodes in Neo4j. Example: `"description"`.

## Application Configuration

- **`TOP_CHUNKS`**: The number of top chunks to process. Default: `3`.
- **`TOP_COMMUNITIES`**: The number of top communities to process. Default: `3`.
- **`TOP_INSIDE_RELS`**: The number of top inside relationships to process. Default: `10`.
- **`TOP_OUTSIDE_RELS`**: The number of top outside relationships to process. Default: `10`.

## Azure Machine Learning Configuration

- **`AML_GRAPH_INDEXER_IMAGE_NAME`**: The name of the AML graph indexer image. This should be an Azure ML environment.
- **`AML_DOCUMENT_PROCESSOR_IMAGE_NAME`**: The name of the AML document processor image. This should be an Azure ML environment.
- **`AML_WORKSPACE_NAME`**: The name of the AML workspace. 
- **`AML_RESOURCE_GROUP`**: The resource group for the AML workspace.
- **`AML_SUBSCRIPTION_ID`**: The subscription ID for the AML workspace.
- **`AML_COMPUTE_NAME`**: The name of the AML compute cluster.
- **`AML_DOCUMENT_DATASET_NAME`**: The name of the document dataset. 
- **`AML_SCG_DATASET_NAME`**: The name of the SCG dataset.

# Contributing
We welcome contributions! Please see the CONTRIBUTING.md file for guidelines.

# License
This project is licensed under the MIT License. See the LICENSE file for details.
## Notes

- Create and update a `.env` file with your specific configuration before running the application.
