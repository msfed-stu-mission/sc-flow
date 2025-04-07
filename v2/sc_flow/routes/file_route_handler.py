# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from fastapi import APIRouter, File, UploadFile, HTTPException
from sc_flow.data.sql import SessionDep, UserFileInteractions
from sc_flow.data import Ack, FileUploadedAck, FilesUploadedAck, FilesRetrieved, FileRetrieved, FileSelected
from sc_flow.utils import create_service_sas_blob
from azure.storage.blob import BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from sqlmodel import select, desc
from typing import List
from datetime import datetime
import logging
import uuid
import os

router = APIRouter(
            prefix='/documents',
            tags = ['Documents']
        )

def _get_container_client():
    return ContainerClient(os.environ["DOCUMENT_CACHE_URI"],
                           os.environ["DOCUMENT_CACHE_CONTAINER"],
                           credential=DefaultAzureCredential())

def _get_blob_client(blob_name):
    return BlobClient(
            os.environ["DOCUMENT_CACHE_URI"],
            os.environ["DOCUMENT_CACHE_CONTAINER"],
            blob_name,
            credential = DefaultAzureCredential()
        )

def _upload_file(file: UploadFile) -> bool:
    try:
        adls_client = _get_blob_client(file.filename)

        if adls_client.exists():
            adls_client.delete_blob()
        adls_client.create_append_blob()

        while contents := file.file.read(1024 * 1024):
            adls_client.append_block(contents)

        logging.info(f"File uploaded successfully: {file.filename}")
        return True
    except Exception as e:
        logging.error(f"Error uploading file {file.filename}: {e}")
        return False
    finally:
        file.file.close()

@router.post(
    "/upload-document",
    summary="Upload a single document to the document cache",
    description="""
       SC-Flow is intended to analyze user documents and apply a security classification label.
       This method allows API access to upload a document for processing.
    """,
    response_model=FileUploadedAck,
    responses={200: {"model": FileUploadedAck}},
)
async def upload_file(req: UploadFile = File(...)):
    logging.info(f"Received file upload request for: {req.filename}")
    if _upload_file(req):
        file_size = os.path.getsize(req.filename)
        return FileUploadedAck(
            file_uploaded=True,
            file_name=req.filename,
            file_size=file_size,
            file_container=os.environ["DOCUMENT_CACHE_CONTAINER"]
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to upload the file")

@router.post(
    "/upload-documents",
    summary="Upload multiple documents to the document cache",
    description="""
       SC-Flow is intended to analyze user documents and apply a security classification label.
       This method allows API access to upload several documents at once for processing.
    """,
    response_model=FilesUploadedAck,
    responses={200: {"model": FilesUploadedAck}},
)
async def upload_file(req: List[UploadFile] = File(...)):
    logging.info(f"Received upload requests for {len(req)} files")
    uploaded_files = []
    error_files = []
    total_size = 0

    for _file in req:
        if _upload_file(_file):
            uploaded_files.append(_file.filename)
            total_size += os.path.getsize(_file.filename)
        else:
            error_files.append(_file.filename)

    all_files_uploaded = len(error_files) == 0

    return FilesUploadedAck(
        all_files_uploaded=all_files_uploaded,
        uploaded_file_names=uploaded_files,
        error_file_names=error_files,
        total_upload_size=total_size,
        file_container=os.environ["DOCUMENT_CACHE_CONTAINER"]
    )

@router.get(
    "/get-available-documents",
    summary="Retrieve urls for all available documents in the doc cache",
    description="""
       SC-Flow is intended to analyze user documents and apply a security classification label.
       This method allows API access to retrieve URLs for all available documents to analyze.
    """,
    response_model=FilesRetrieved,
    responses={200: {"model": FilesRetrieved}}
)
async def get_all_available_docs():
    container_client = _get_container_client()
    return FilesRetrieved(
        files=[
            FileRetrieved(file_name=blob.name, file_url=create_service_sas_blob(_get_blob_client(blob.name), os.environ["DOCUMENT_CACHE_KEY"])) 
            for blob in container_client.list_blobs()
        ]
    )


@router.post(
    "/document-selected",
    summary="Alert that a user has selected a file for potential analysis",
    description="""
       To facilitate interactive analysis, SCFlow will automatically detect when a user is
       viewing a document, with the expectation that the user will leverage the SCFlow agents to 
       analyze that document.
    """,
    response_model=Ack,
    responses={200: {"model": Ack}},
)
async def handle_selection(selection: FileSelected, session: SessionDep) -> Ack:
    ufi = UserFileInteractions(session_id = uuid.uuid4().hex, 
                                file_url = selection.file_url, 
                                timestamp = datetime.utcnow())
    session.add(ufi)
    session.commit()
    session.refresh(ufi)
    return Ack(ack=True)

@router.get(
    "/get-latest-interaction",
    summary="Retrieve the latest user/file interaction",
    description="""
       The SCFlow agent will keep track of which file is currently being interacted with by checking the 
       user/file interaction logs. 
    """,
    response_model=UserFileInteractions,
    responses={200: {"model": UserFileInteractions}}
)
async def get_latest_select(session: SessionDep):
    ufi = session.exec(select(UserFileInteractions).order_by(desc(UserFileInteractions.timestamp)).limit(1)).all()[0]
    return ufi