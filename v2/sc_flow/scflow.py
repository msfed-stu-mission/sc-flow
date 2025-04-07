# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from dotenv import load_dotenv
load_dotenv() # pylint: disable=wrong-import-position

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables.graph import MermaidDrawMethod
from contextlib import asynccontextmanager
from sc_flow.utils.checkpoint.aio import AsyncCosmosDBMongoDBSaver
from sc_flow.data.sql import create_db_and_tables
from sc_flow.routes import file_router
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from langgraph.types import Command
from sc_flow.agents import graph as scf
from sc_flow.utils import configure_logging, _set_if_undefined
import asyncio
import uvicorn
import logging
import os

local_mode = True 

configure_logging(log_level=logging.INFO)

async def stream_graph_updates(user_input: str, graph):
    config = {"configurable": {"thread_id": "1"}}
    async for event in graph.astream({"messages": [("user", user_input)]}, config, stream_mode="updates"):
        for value in event.values():
            if "messages" not in value:
                continue
            #print("Assistant:", value["messages"][-1].content)
            print(value)
    if len(graph.get_state(config).next) > 0:
        user_input_val = input(f"{value[0].value}\n")  
        async for event in graph.astream(Command(resume=user_input_val), config, stream_mode="updates"):
            for value in event.values():
                if "messages" not in value:
                    continue
                #print("Assistant:", value["messages"][-1].content)
                print(value)

def run_local():
    graph = scf.get_or_build_graph()

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        asyncio.run(stream_graph_updates(user_input, graph))

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncCosmosDBMongoDBSaver.from_conn_string(
        f"mongodb://{os.getenv('MONGODB_USER')}:{os.getenv('MONGODB_PASSWORD')}@{os.getenv('MONGODB_HOST')}:{os.getenv('MONGODB_PORT')}/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@{os.getenv('MONGODB_DATABASE')}@"
    ) as checkpointer:
        workflow = scf.get_graph_builder()
        graph = workflow.compile(checkpointer=checkpointer)
        create_db_and_tables()

        sdk = CopilotKitRemoteEndpoint(
            agents=[
                LangGraphAgent(
                    name="scflow",
                    description="This agent workflow specializes in security classification for documents.",
                    graph=graph,
                )
            ],
        )
        
        app.include_router(file_router)
        add_fastapi_endpoint(app, sdk, "/scflow", max_workers=os.environ.get("APPLICATION_MAX_WORKERS", 10))
        yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],  
        allow_headers=["*"], 
    )

def main():
    logging.info("Starting up SC-Flow...")

    _set_if_undefined("AZURE_CLIENT_ID")
    _set_if_undefined("AZURE_TENANT_ID")
    _set_if_undefined("AZURE_CLIENT_SECRET")

    _set_if_undefined("DOCUMENT_CACHE_URI")
    _set_if_undefined("DOCUMENT_CACHE_KEY")
    _set_if_undefined("DOCUMENT_CACHE_CONTAINER")
    _set_if_undefined("DOCUMENT_CACHE_FOLDER")

    if local_mode:
        run_local()
    else:        
        _set_if_undefined("MONGODB_USER")
        _set_if_undefined("MONGODB_PASSWORD")
        _set_if_undefined("MONGODB_HOST")
        _set_if_undefined("MONGODB_PORT")
        _set_if_undefined("MONGODB_DATABASE")

        port = int(os.getenv("APPLICATION_PORT", "8000"))
        uvicorn.run(
            "sc_flow.scflow:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=(
                ["."] 
            )
        )

if __name__ == "__main__":
    main()
