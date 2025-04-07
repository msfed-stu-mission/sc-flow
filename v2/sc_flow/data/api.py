# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pydantic import BaseModel, Field
from typing import Optional, List

class Ack(BaseModel):
    ack: bool = Field(..., description="Acknowledge the action has occurred")

class FileUploadedAck(BaseModel):
    file_uploaded: bool = Field(..., description="Was the file uploaded successfully?")
    file_name: str = Field(..., description="The name of the file that has been uploaded")
    file_size: int = Field(..., description="The size of the file in bytes")
    file_container: str = Field(..., description="The name of the ADLS Gen2 container where the file has been uploaded")

class FilesUploadedAck(BaseModel):
    all_files_uploaded: bool = Field(..., description="Were the files uploaded successfully?")
    uploaded_file_names: List[str] = Field(..., description="The names of the files that have been uploaded")
    error_file_names: List[str] = Field(..., description="The names of the files that have NOT been uploaded")
    total_upload_size: int = Field(..., description="The size of the file in bytes")
    file_container: str = Field(..., description="The name of the ADLS Gen2 container where the file has been uploaded")

class FileSelected(BaseModel):
    file_url: str = Field(None, description="The url of the selected file")

 
class FileRetrieved(BaseModel):
    file_name: str = Field(..., description="The name of the retrieved file")
    file_url: str = Field(..., description="The url of the retrieved file")

class FilesRetrieved(BaseModel):
    files: List[FileRetrieved] = Field(..., description="A collection of retrieved files")