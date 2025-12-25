from typing import List, Dict, Any
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

    def retrieve_relevant_schema(self, user_query: str, top_k: int = 15) -> Dict[str, Any]:
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

    def _format_output_for_llm(
        self,
        tables: Dict[str, Dict],
        matched_cols: List[str]
    ) -> Dict[str, Any]:
        """Constructs a clean JSON representation for the SQL Agent."""

        if not tables:
            return {
                "status": "empty",
                "message": "No relevant tables found.",
                "matched_columns": matched_cols,
                "tables": []
            }

        result = {
            "status": "ok",
            "matched_columns": matched_cols,
            "tables": []
        }

        for table_name, schema in tables.items():
            table_obj = {
                "table_name": table_name,
                "description": schema.get("description"),
                "columns": [],
                "relationships": []
            }

            # Columns
            for col in schema.get("columns", []):
                table_obj["columns"].append({
                    "name": col.get("name"),
                    "type": col.get("type")
                })

            # Foreign keys / relationships
            for fk in schema.get("foreign_keys", []):
                table_obj["relationships"].append({
                    "column": fk.get("col"),
                    "references_table": fk.get("foreign_table")
                })

            result["tables"].append(table_obj)

        return result
