from typing import List, Dict, Set
from app.vectorstore.qdrant_client import client as qdrant_client
from app.config import settings
from app.utils.logging_util import logger
from sentence_transformers import SentenceTransformer

class SchemaRetrievalService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.collection_name = settings.DB_COLLECTION_NAME

    def _get_table_by_name(self, table_name: str) -> Dict:
        """
        Fetches the full table schema from Qdrant using a filter.
        In a production environment, you might cache this in Redis.
        """
        result = qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "type", "match": {"value": "table"}},
                    {"key": "table_name", "match": {"value": table_name}}
                ]
            },
            limit=1,
            with_payload=True
        )
        points = result[0]
        return points[0].payload["full_schema"] if points else None

    def retrieve_relevant_schema(self, user_query: str, top_k: int = 15) -> str:
        """
        The core Hierarchical Retrieval logic.
        """
        logger.info(f"🔍 Searching schema for: {user_query}")
        
        # 1. Vectorize the User Query
        query_vector = self.model.encode(user_query).tolist()

        # 2. Perform Search
        search_results = qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        relevant_tables: Dict[str, Dict] = {}
        matched_columns: List[str] = []

        # 3. Process results
        for hit in search_results.points:
            payload = hit.payload
            t_name = payload["table_name"]

            if payload["type"] == "table":
                # If we hit a table directly, add its full schema
                if t_name not in relevant_tables:
                    relevant_tables[t_name] = payload["full_schema"]
            
            elif payload["type"] == "column":
                # If we hit a column, we need to ensure its parent table is included
                matched_columns.append(f"{t_name}.{payload['column_name']}")
                if t_name not in relevant_tables:
                    parent_schema = self._get_table_by_name(t_name)
                    if parent_schema:
                        relevant_tables[t_name] = parent_schema

        # 4. Format for LLM Prompt
        return self._format_output_for_llm(relevant_tables, matched_columns)

    def _format_output_for_llm(self, tables: Dict[str, Dict], matched_cols: List[str]) -> str:
        """Constructs a clean string representation for the SQL Agent."""
        if not tables:
            return "No relevant tables found."

        output = "### RELEVANT SCHEMA CONTEXT ###\n"
        output += f"High-priority column matches: {', '.join(matched_cols)}\n\n"

        for t_name, schema in tables.items():
            output += f"Table: {t_name}\n"
            if schema.get('description'):
                output += f"Description: {schema['description']}\n"
            
            col_lines = [f"  - {c['name']} ({c['type']})" for c in schema['columns']]
            output += "Columns:\n" + "\n".join(col_lines) + "\n"
            
            if schema.get('foreign_keys'):
                output += "Relationships:\n"
                for fk in schema['foreign_keys']:
                    output += f"  - {fk['col']} -> {fk['foreign_table']}\n"
            output += "---\n"
        
        return output