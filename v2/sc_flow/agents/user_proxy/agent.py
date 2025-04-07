# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from ..state import State, Router
from .prompt import prompt
from sc_flow.agents.base_agent import BaseAgent
from sc_flow.utils import llm_generator
from sc_flow.data.sql import get_session, UserFileInteractions
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages.ai import AIMessage
from sqlmodel import select, desc
import os

def get_current_doc():
    ufi = next(get_session()).exec(select(UserFileInteractions).order_by(desc(UserFileInteractions.timestamp)).limit(1)).all()[0]
    if ufi.file_url is None:
        return ""
    return ufi.file_url.split("?")[0].split("/")[-1]

class ProxyOrchestratorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm)
        self.build()

    def build(self):
        self._chain = (
            {
                "request": RunnablePassthrough(),
                "document_name": lambda x: get_current_doc()
            }
            | prompt 
            | self.llm.with_structured_output(Router)
        )


    async def invoke_chain(self, query: str):
        """
        Executes the chain for security classification guide analysis.

        :param question: The user’s question.
        :return: An AI-generated response.
        """
        
        resp = await self.chain.ainvoke(query)
        return AIMessage(content=resp["response"]), resp["next_agent"], resp["selected_document_name"]
    
async def user_proxy(state: State):
    proxy_agent = ProxyOrchestratorAgent(llm=llm_generator())
    resp, next_agent, doc_name = await proxy_agent(state["messages"])
    return {
        "last_user_message": state["messages"][-1],
        "messages": [resp],
        "next_agent": next_agent,
        "ctx_doc": doc_name,
        "logs": [] 
    }