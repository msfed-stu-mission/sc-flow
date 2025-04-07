# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from typing import Annotated, Optional
from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine
from sqlalchemy import TIMESTAMP, Column
from datetime import datetime

class UserFileInteractions(SQLModel, table=True):
    session_id: Optional[str] = Field(default=None, primary_key=True)
    file_url: Optional[str] = Field(default=None, index=True)
    timestamp: Optional[datetime] = Field(default=None, sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )) 

sqlite_file_name = "user_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
