# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from abc import ABC
from langchain_core.language_models.chat_models import BaseChatModel
from sc_flow.utils import configure_logging
import logging
configure_logging()

class BaseAgent(ABC):
    def __init__(self, llm: BaseChatModel):
        """
        Initialize a base agent with a language model.

        :param llm: BaseChatModel - Language model instance.
        """
        self._llm = llm
        self._chain = None

    def build(self):
        """
        Construct the agent chain. The chain object should be set in this method.
        """
        raise NotImplementedError("This method has not been implemented.")
    
    @property
    def llm(self):
        return self._llm
    
    @property
    def chain(self):
        if self._chain is None:
            logging.warning("This agent has not been built, and the chain does not exist!")
        return self._chain
        
    async def __call__(self, query: str) -> str:
        return await self.invoke_chain(query)

    async def invoke_chain(self, query: str) -> str:
        """
        Helper to invoke a chain with a query.

        :param query: The user’s input query.
        :return: The chain response.
        """
        raise NotImplementedError("This method has not been implemented.")