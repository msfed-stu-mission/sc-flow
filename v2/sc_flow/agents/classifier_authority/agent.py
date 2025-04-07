# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
from sc_flow.agents.state import ExpertAnalysisState, State
from langchain_core.runnables import RunnablePassthrough, RunnableConfig



"""
from .prompt import prompt

from sc_flow.agents.state import State, ClassificationDecision, ExpertResponse, ExpertAnalysisState
from sc_flow.utils import llm_generator, neo4j_vector_generator
from sc_flow.utils import llm_generator
from langchain_core.runnables import RunnablePassthrough, RunnableConfig
from langchain.chains.router.multi_retrieval_qa import MultiRetrievalQAChain

from copilotkit.langgraph import copilotkit_emit_state
from langchain.chains import RetrievalQA
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from langchain_core.prompts import ChatPromptTemplate

import ast
import os

get_unclass_details_prompt = """
You are an analyst specializaing in classification protocols, security policies, 
and regulatory frameworks. 
The knowledge graph contains detailed representations of classification criteria, 
relationships, and hierarchies for securing sensitive information. 
Your task is to retrieve all criteria required to classify information as 
**Unclassified** based on the following guidelines:

Scope of Retrieval:

Include all explicit criteria directly related to Unclassified designation.

Attributes to Retrieve:

Criterion name and description.
Regulatory references or definitions (e.g., "EO 13526" or public access laws like FOIA).
Conditions that make information publicly releasable.
Limitations or restrictions for Unclassified information (e.g., "For Official Use Only").
Relationships to Explore:

Downward dependencies from higher classifications (e.g., what explicitly precludes Secret, Top Secret).
Relationships to public information policies, transparency guidelines, and open data standards.
Caveats for controlled unclassified information (CUI) or other nuanced designations.
Metadata:

Include sources or citations for each criterion.
Note any relationships to laws or policies governing public dissemination.
Highlight any exceptions or situations where unclassified information is still restricted.
Output Format:

Summarize the criteria in structured fields (e.g., "Name," "Description," "Public Availability").
Clearly differentiate Unclassified information from related categories like Controlled Unclassified Information (CUI) or Sensitive but Unclassified (SBU).
Based on this input, provide a response that comprehensively defines the criteria for information to be classified as Unclassified, ensuring clarity and completeness.

Be comprehensive and do not include anything else in your response besides the critera.
"""

get_s_details_prompt = """
You are an analyst specializaing in classification protocols, security policies, 
and regulatory frameworks. 
The knowledge graph contains detailed representations of classification criteria, 
relationships, and hierarchies for securing sensitive information. 
Your task is to retrieve all criteria required to classify information as 
**Secret** based on the following guidelines:

Scope of Retrieval:

Include all explicit criteria directly related to Secret classification.
Attributes to Retrieve:

Criterion name and description.
Regulatory reference (e.g., "Executive Order 13526").
Specific conditions (e.g., "could cause serious damage to national security").
Thresholds or levels of risk (e.g., "serious damage" vs. "exceptionally grave damage").
Relationships to Explore:

Parent-child relationships between classification levels.
Dependencies (e.g., legal mandates, organizational policies).
Exceptions or caveats (e.g., downgrade conditions or special cases).
Metadata:

Include sources or citations for each criterion.
Highlight relationships that define precedence or hierarchical importance.
Output Format:

Summarize the criteria in structured fields (e.g., "Name," "Description," "Risk Level," "Conditions").
Group criteria by overarching themes (e.g., "National Security," "Economic Security").
Based on this input, provide a response that captures all relevant information and ensures completeness. 
If applicable, explain how the relationships and dependencies contribute to the classification as Secret.

Be comprehensive and do not include anything else in your response besides the critera.
"""
get_ts_details_prompt = """
You are an analyst specializaing in classification protocols, security policies, 
and regulatory frameworks. 
The knowledge graph contains detailed representations of classification criteria, 
relationships, and hierarchies for securing sensitive information. 
Your task is to retrieve all criteria required to classify information as 
**Top Secret** based on the following guidelines:

Scope of Retrieval:

Include all explicit criteria directly related to Top Secret classification.
Attributes to Retrieve:

Criterion name and description.
Regulatory reference (e.g., "Executive Order 13526").
Specific conditions (e.g., "could cause exceptionally grave damage to national security").
Thresholds or levels of risk (e.g., "grave damage" vs. "serious damage").
Relationships to Explore:

Parent-child relationships between classification levels.
Dependencies (e.g., legal mandates, organizational policies).
Exceptions or caveats (e.g., downgrade conditions or special cases).
Metadata:

Include sources or citations for each criterion.
Highlight relationships that define precedence or hierarchical importance.
Output Format:

Summarize the criteria in structured fields (e.g., "Name," "Description," "Risk Level," "Conditions").
Group criteria by overarching themes (e.g., "National Security," "Intelligence Operations," "Allied Trust").
Based on this input, provide a response that captures all relevant information and ensures completeness. 
If applicable, explain how the relationships and dependencies contribute to the classification as Top Secret.

Be comprehensive and do not include anything else in your response besides the critera.
"""

ts_evaluator_prompt = ChatPromptTemplate([
    ("system", """ 
    You are an expert in determining whether or not textual content contains information that is classified at the Top Secret level. 
    If any of the content in the text is considered Top Secret, the entire text is considered classified at Top Secret.
    When giving your reasoning for your classification decision, be extremely explicit and cite examples.
    Examples of content that would constitute Top Secret material include: 

    {context}
    """), 
    ("user", """{content}""")
])

s_evaluator_prompt = ChatPromptTemplate([
    ("system", """ 
    You are an expert in determining whether or not textual content contains information that is classified at the Secret level. 
    If any of the content in the text is considered Secret, the entire text is considered classified at Secret.
    When giving your reasoning for your classification decision, be extremely explicit and cite examples.
    Examples of content that would constitute Secret material include: 

    {context}
    """),
    ("user", """{content}""")
])

unclass_evaluator_prompt = ChatPromptTemplate([
    ("system", """ 
    You are an expert in determining whether or not textual content contains information that is unclassified or controlled unclassified information. 
    If any of the content in the text is NOT unclassified, the entire text is considered classified at some level.
    When giving your reasoning for your classification decision, be extremely explicit and cite examples.
    Examples of content that would constitute classified material include: 

    {context}
     
    """),
    ("user", """{content}""")
])

agent_prompt = ChatPromptTemplate([
    ("system", """ 
    You are the final decision authority on the level of classification (Top Secret, Secret, or Unclassified/CUI)
    to which a given document belongs. 
    You will be given an extensive set of context pertaining to classification levels and their varying criteria, as 
     well as a body of text to evaluate against the criteria. You will return a final classification decision
     as well as an elaborate explanation of your decision.
     
     Classification context:
     {top_secret_context}
     {secret_context}
     {unclassified_context}

    """), 
    ("user", """ 

     Document contents:
     {content}

    Classification Decision:
    Explanation: 
     """)
])

async def classifier_authority(state: ExpertAnalysisState, config: RunnableConfig) -> State:
    llm = llm_generator()

    classification_decisions = dict(state['classification_analysis'])
    security_classifier_chain = (
        {
            "unclass_expert_recommendations": lambda x: classification_decisions['unclass_expert_agent'],
            "secret_expert_recommendations": lambda x: classification_decisions['secret_expert_agent'],
            "top_secret_expert_recommendations": lambda x: classification_decisions['top_secret_expert_agent'],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    resp = await security_classifier_chain.ainvoke(state['user_query'])
    return {
        'messages': AIMessage(content=resp),
        'next_agent': 'user_proxy',
        'logs': state['inner_state']['logs']
    }

def get_search_client():
    search_client = SearchClient(os.environ["AI_SEARCH_ENDPOINT"], 
                                 os.environ["AI_SEARCH_INDEX"], 
                                 AzureKeyCredential(os.environ["AI_SEARCH_KEY"]))
    return search_client

async def evaluator(state: State, config: RunnableConfig):
    #await copilotkit_emit_state(config, state)

    topChunks = os.environ.get("TOP_CHUNKS", 3)
    topCommunities = os.environ.get("TOP_COMMUNITIES", 3)
    topInsideRels = os.environ.get("TOP_INSIDE_RELS", 10)
    topOutsideRels = os.environ.get("TOP_OUTSIDE_RELS", 10)

    search_client = get_search_client()
    store = neo4j_vector_generator(topChunks, topCommunities, topOutsideRels, topInsideRels)
    llm = llm_generator()
    """
    ctxs = []
    for prompt in [get_ts_details_prompt, get_s_details_prompt, get_unclass_details_prompt]:
        graph_chain = RetrievalQA.from_chain_type(
            llm, chain_type="stuff", retriever=store.as_retriever()
        )
        
        ctx = await graph_chain.ainvoke({"query":prompt}, 
                                return_only_outputs=True)
        ctxs += [ctx["result"]]
    """
    agent_chain = (
        {
            "top_secret_context": lambda x: store.as_retriever().get_relevant_documents(get_ts_details_prompt),
            "secret_context": lambda x: store.as_retriever().get_relevant_documents(get_s_details_prompt),
            "unclassified_context": lambda x: store.as_retriever().get_relevant_documents(get_unclass_details_prompt),
            "content": RunnablePassthrough()
        }
        | agent_prompt
        | llm
    )

    content = []
    async with search_client:
        results = await search_client.search(search_text=state['ctx_doc'])
        async for result in results:
            metadata = ast.literal_eval(result["metadata"])
            if metadata["doc_name"] != state['ctx_doc']:
                continue
            content += [result["content"]]

    decision = await agent_chain.ainvoke("\n".join(content), return_only_outputs=True)
    print(decision)
    return {
        "messages": decision
    }