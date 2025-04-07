# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

def get_retrieval_query(topChunks: int, 
                        topCommunities: int, 
                        topOutsideRels: int, 
                        topInsideRels: int) -> str:
    retrieval_query = """
        WITH collect(node) as nodes
        WITH
        collect {
            UNWIND nodes as n
            MATCH (n)<-[]->(c:Document)
            WITH c, count(distinct n) as freq
            RETURN c.text AS chunkText
            ORDER BY freq DESC
            LIMIT """ +topChunks+ """
        } AS text_mapping,
        collect {
            UNWIND nodes as n
            MATCH (n)-[:IN_COMMUNITY]->(c:__Community__)
            WITH c, c.community_rank as rank, c.weight AS weight
            WHERE c.summary is not null
            RETURN c.summary 
            ORDER BY rank, weight DESC
            LIMIT """ +topCommunities+ """
        } AS report_mapping,
        // Outside Relationships 
        collect {
            UNWIND nodes as n
            MATCH (n)-[r]-(m) 
            WHERE NOT m IN nodes
            RETURN type(r) AS descriptionText
            LIMIT """ +topOutsideRels+ """
        } as outsideRels,
        collect {
            UNWIND nodes as n
            MATCH (n)-[r]-(m) 
            WHERE m IN nodes
            RETURN type(r) AS descriptionText
            LIMIT """ +topInsideRels+ """
        } as insideRels,
        collect {
            UNWIND nodes as n
            RETURN n.id AS descriptionText
        } as entities
        RETURN {Chunks: text_mapping, Reports: report_mapping, 
            Relationships: outsideRels + insideRels, 
            Entities: entities} AS text, 1.0 AS score, {} AS metadata
    """
    return retrieval_query