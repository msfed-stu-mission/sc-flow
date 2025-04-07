# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from langchain_core.prompts import ChatPromptTemplate

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
