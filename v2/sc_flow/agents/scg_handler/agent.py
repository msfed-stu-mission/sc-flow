# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from ..state import State
from .prompt import prompt
from sc_flow.agents.base_agent import BaseAgent
from sc_flow.utils import llm_generator, neo4j_vector_generator
from langchain_community.vectorstores import Neo4jVector
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os

class SCGAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, store: Neo4jVector):
        """
        Initialize SCGAgent with an LLM and a Neo4j retriever store.

        :param llm: Language model instance.
        :param store: Retriever store for contextual information.
        """
        super().__init__(llm)
        self._store = store
        self.build()

    def build(self):
        self._chain = (
            {
                "context": self.store.as_retriever(),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

    @property
    def store(self) -> Neo4jVector:
        return self._store
    
    async def invoke_chain(self, query: str) -> AIMessage:
        """
        Executes the chain for security classification guide analysis.

        :param question: The user’s question.
        :return: An AI-generated response.
        """
        
        resp = await self.chain.ainvoke(query)
        return AIMessage(content=resp)
    

async def scg_analyst(state: State):
    topChunks = os.environ.get("TOP_CHUNKS", 3)
    topCommunities = os.environ.get("TOP_COMMUNITIES", 3)
    topInsideRels = os.environ.get("TOP_INSIDE_RELS", 10)
    topOutsideRels = os.environ.get("TOP_OUTSIDE_RELS", 10)

    agent = SCGAgent(llm_generator(), 
                     neo4j_vector_generator(topChunks, topCommunities, topOutsideRels, topInsideRels)
            )
    
    resp = await agent(state['last_user_message'].content)
    state['messages'] += [resp]
    state['next_agent'] = "user_proxy"
    return state