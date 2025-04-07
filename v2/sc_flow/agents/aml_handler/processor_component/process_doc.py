# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from llmsherpa.readers import LayoutPDFReader
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.docstore.document import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import AzureOpenAIEmbeddings
import mlflow
import os 


def _make_doc(sas_uri, chunks):
    return [Document(
                    page_content=chunk.to_context_text(),
                    metadata={
                        "source": sas_uri,
                        "doc_name": sas_uri.split("/")[-1],
                        "chunk_number": chunk_num,
                        "chunk_type": chunk.tag,
                        "page": chunk.page_idx,
                        "bbox": chunk.bbox,
                        "block_idx": chunk.block_idx,
                        "level": chunk.level
                    },
                ) for chunk_num, chunk in enumerate(chunks)]
    
async def process_doc():
    sas_uris = os.environ.get("DOCUMENT_SAS_URLS", None)
    if not sas_uris:
        raise KeyError("Missing required environment variable: DOCUMENT_SAS_URLS")
    
    with mlflow.start_run():
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.environ["EMBEDDING_DEPLOYMENT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )

        semantic_splitter = SemanticChunker(
            embeddings, 
            breakpoint_threshold_type="gradient"
        )

        vector_store: AzureSearch = AzureSearch(
            azure_search_endpoint=os.environ["AI_SEARCH_ENDPOINT"],
            azure_search_key=os.environ["AI_SEARCH_KEY"],
            index_name=os.environ["AI_SEARCH_INDEX"],
            embedding_function=embeddings.embed_query,
        )

        reader = LayoutPDFReader(os.environ["NLM_INGESTOR_ENDPOINT"])
        for sas_uri in sas_uris.split(","):
            chunks = reader.read_pdf(sas_uri).chunks()
            vector_store.add_documents(documents=_make_doc(sas_uri.split("?")[0], chunks))
