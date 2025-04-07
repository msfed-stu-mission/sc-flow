from langchain_core.prompts import ChatPromptTemplate

graph_system_prompt = (
    "# Knowledge Graph Extraction for Security Classification\n"
    "## 1. Overview\n"
    "You are an advanced system designed to extract structured information "
    "from unstructured text to build a **security classification knowledge graph**. "
    "The text will describe guidelines for classifying information into categories "
    "such as **Unclassified**, **Controlled Unclassified Information (CUI)**, **Secret (S)**, "
    "and **Top Secret (TS)**. Your task is to accurately identify key entities, "
    "their attributes, and relationships while ensuring the graph structure is simple, "
    "consistent, and clear.\n"
    "\n"
    "## 2. Entities and Relationships\n"
    "- **Entities** represent:\n"
    "  - **Classification Levels**: Categories like 'Unclassified,' 'CUI,' 'Secret,' 'Top Secret.'\n"
    "  - **Criteria**: Specific conditions or rules determining classification levels.\n"
    "  - **Attributes**: Characteristics or additional details about the classification or criteria.\n"
    "- **Relationships** describe connections between entities:\n"
    "  - **DEFINED_BY**: Links classification levels to the criteria that define them.\n"
    "  - **APPLICABLE_TO**: Links criteria to entities they apply to (e.g., individuals, systems, scenarios).\n"
    "  - **HAS_ATTRIBUTE**: Links entities to their attributes or properties.\n"
    "\n"
    "## 3. Guidelines for Graph Construction\n"
    "- All entities and relationships MUST have at least one property called **description**, which provides a textual description of the entity or relationship. Additional properties are acceptable.\n"
    "- The key entities we want in the graph are **CUI**, **Unclassified**, **Secret**, and **Top Secret**. These will be the core community anchors.\n"
    "- Use **general and timeless relationship types**.\n"
    "- **Coreference Resolution**: If an entity appears multiple times in the text under different names or pronouns, "
    "use the **most complete and consistent name** for the entity.\n"
    "- Ensure **clarity and accessibility** by using simple, human-readable labels for all entities and relationships.\n"
    "\n"
    "## 4. Examples\n"
    "\n"
    "### Example 1:\n"
    "Text:\n"
    "\"Information pertaining to the development of nuclear weapons must be classified as Top Secret "
    "if it could reasonably be expected to cause exceptionally grave damage to national security.\"\n"
    "\n"
    "Graph:\n"
    "- Entities:\n"
    "  - 'Top Secret' (Classification Level)\n"
    "  - 'Nuclear weapons development' (Criteria)\n"
    "  - 'Exceptionally grave damage' (Attribute)\n"
    "- Relationships:\n"
    "  - 'Top Secret' DEFINED_BY 'Nuclear weapons development'\n"
    "  - 'Nuclear weapons development' HAS_ATTRIBUTE 'Exceptionally grave damage'\n"
    "\n"
    "### Example 2:\n"
    "Text:\n"
    "\"Documents containing personally identifiable information (PII) must be marked as Controlled Unclassified "
    "Information (CUI) to ensure privacy.\"\n"
    "\n"
    "Graph:\n"
    "- Entities:\n"
    "  - 'Controlled Unclassified Information' (Classification Level)\n"
    "  - 'Personally Identifiable Information' (Criteria)\n"
    "  - 'Privacy' (Attribute)\n"
    "- Relationships:\n"
    "  - 'Controlled Unclassified Information' DEFINED_BY 'Personally Identifiable Information'\n"
    "  - 'Personally Identifiable Information' HAS_ATTRIBUTE 'Privacy'\n"
    "\n"
    "### Example 3:\n"
    "Text:\n"
    "\"Unclassified information is publicly available and poses no risk to national security.\"\n"
    "\n"
    "Graph:\n"
    "- Entities:\n"
    "  - 'Unclassified' (Classification Level)\n"
    "  - 'Publicly available' (Criteria)\n"
    "  - 'No risk to national security' (Attribute)\n"
    "- Relationships:\n"
    "  - 'Unclassified' DEFINED_BY 'Publicly available'\n"
    "  - 'Publicly available' HAS_ATTRIBUTE 'No risk to national security'\n"
    "\n"
    "### Example 4:\n"
    "Text:\n"
    "\"Communication protocols used in classified systems must be Secret or higher "
    "to prevent unauthorized access.\"\n"
    "\n"
    "Graph:\n"
    "- Entities:\n"
    "  - 'Secret' (Classification Level)\n"
    "  - 'Communication protocols' (Criteria)\n"
    "  - 'Prevent unauthorized access' (Attribute)\n"
    "- Relationships:\n"
    "  - 'Secret' DEFINED_BY 'Communication protocols'\n"
    "  - 'Communication protocols' HAS_ATTRIBUTE 'Prevent unauthorized access'\n"
    "\n"
    "### Example 5:\n"
    "Text:\n"
    "\"Top Secret documents require two-person integrity controls to access, "
    "ensuring the highest security standards.\"\n"
    "\n"
    "Graph:\n"
    "- Entities:\n"
    "  - 'Top Secret' (Classification Level)\n"
    "  - 'Two-person integrity controls' (Criteria)\n"
    "  - 'Highest security standards' (Attribute)\n"
    "- Relationships:\n"
    "  - 'Top Secret' DEFINED_BY 'Two-person integrity controls'\n"
    "  - 'Two-person integrity controls' HAS_ATTRIBUTE 'Highest security standards'\n"
    "\n"
    "## 5. Strict Compliance\n"
    "- Follow the provided examples and rules precisely.\n"
    "- Do not introduce any information not explicitly stated in the text.\n"
    "- If uncertain, prioritize clarity and generality in constructing the graph.\n"
)

graph_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            graph_system_prompt,
        ),
        (
            "human",
            (
                "Tip: Make sure to answer in the correct format and do "
                "not include any explanations. "
                "Use the given format to extract information from the "
                "following input: {input}"
            ),
        ),
    ]
)

dedup_system_prompt = """You are a data processing assistant. Your task is to identify duplicate entities in a list and decide which of them should be merged.
The entities might be slightly different in format or content, but essentially refer to the same thing. Use your analytical skills to determine duplicates.

Here are the rules for identifying duplicates:
1. Entities with minor typographical differences should be considered duplicates.
2. Entities with different formats but the same content should be considered duplicates.
3. Entities that refer to the same real-world object or concept, even if described differently, should be considered duplicates.
4. If it refers to different numbers, dates, or products, do not merge results
"""
dedup_user_template = """
Here is the list of entities to process:
{entities}

Please identify duplicates, merge them, and provide the merged list.
"""
extraction_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    dedup_system_prompt,
                ),
                (
                    "human",
                    dedup_user_template,
                ),
            ]
        )

community_system_prompt = """Based on the provided nodes and relationships that belong to the same graph community,
generate a natural language summary of the provided information:
{community_info}

Summary:"""

community_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given an input triples, generate the information summary. No pre-amble.",
        ),
        ("human", community_system_prompt),
    ]
)