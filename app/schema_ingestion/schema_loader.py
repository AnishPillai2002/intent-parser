import uuid
import itertools
from typing import Dict, Iterable, List
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, VectorParams, Distance, PayloadSchemaType

# Project Imports
from app.config import settings
from app.vectorstore.qdrant_client import client as qdrant_client
from app.schema_ingestion.schema_extractor import SchemaExtractor 
from app.utils.logging_util import logger 

class SchemaIngestionService:
    def __init__(self, db_url: str = None):
        self.extractor = SchemaExtractor(db_url=db_url)
        
        logger.info("⚙️ Loading Embedding Model: %s", settings.EMBEDDING_MODEL)
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.critical("Failed to load embedding model: %s", e, exc_info=True)
            raise e
            
        self.batch_size = 25 
        self._ensure_collection(settings.DB_COLLECTION_NAME)

    def _ensure_collection(self, collection_name: str):
        """Ensures collection exists and ALL required payload indexes are present."""
        try:
            collections = qdrant_client.get_collections()
            existing_names = {c.name for c in collections.collections}

            if collection_name not in existing_names:
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=settings.VECTOR_SIZE, distance=Distance.COSINE),
                )

            # Create keyword indexes for efficient filtering during retrieval
            for field in ["type", "table_name"]:
                qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            
            logger.info(f"✅ Collection and indexes ready on {collection_name}")
        except Exception as e:
            logger.error(f"Failed to ensure collection or indexes: {e}")
            raise

    def _generate_table_text(self, table: Dict) -> str:
        """Creates a semantic summary for the Table-level node."""
        t_name = table['table_name']
        desc = table.get('description', '')
        cols = ", ".join([c['name'] for c in table['columns']])
        
        text = f"Table: {t_name}. "
        if desc: 
            text += f"Summary: {desc}. "
        text += f"Contains columns: {cols}"
        return text

    def _generate_column_text(self, table_name: str, column: Dict) -> str:
        """
        Contextualized text for the Column-level node.
        Includes sample values to enable 'Value-Aware' retrieval.
        """
        # Prefix with table name to maintain unique context for similar column names
        text = f"Table: {table_name}, Column: {column['name']} (Type: {column['type']})"
        
        # IMPROVEMENT: Add categorical samples to the embedding text
        if column.get('samples'):
            samples_str = ", ".join(column['samples'])
            text += f". Example values: {samples_str}"
            
        return text

    def _batch_iterator(self, iterable: Iterable, size: int):
        it = iter(iterable)
        while True:
            chunk = list(itertools.islice(it, size))
            if not chunk: break
            yield chunk

    def run_ingestion(self):
        """Main entry point: Extract -> Contextualize -> Embed -> Upsert"""
        logger.info("🚀 Starting Advanced Hierarchical Ingestion...")
        
        # Uses the updated generator with pg_stats and TABLESAMPLE logic
        table_generator = self.extractor.extract_schema_generator()
        total_tables = 0
        total_points = 0

        for batch in self._batch_iterator(table_generator, self.batch_size):
            points = []
            
            for table in batch:
                t_name = table['table_name']
                
                # 1. Create TABLE Node
                table_summary = self._generate_table_text(table)
                table_vector = self.model.encode(table_summary).tolist()
                table_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tbl_{t_name}"))
                
                points.append(PointStruct(
                    id=table_id,
                    vector=table_vector,
                    payload={
                        "type": "table",
                        "table_name": t_name,
                        "schema_text": table_summary,
                        "full_schema": table # Store JSON for LLM reference
                    }
                ))

                # 2. Create COLUMN Nodes
                for col in table['columns']:
                    col_text = self._generate_column_text(t_name, col)
                    col_vector = self.model.encode(col_text).tolist()
                    col_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"col_{t_name}_{col['name']}"))
                    
                    points.append(PointStruct(
                        id=col_id,
                        vector=col_vector,
                        payload={
                            "type": "column",
                            "table_name": t_name,
                            "column_name": col['name'],
                            "context_text": col_text,
                            "parent_table_id": table_id,
                            "samples": col.get('samples', []) # Store samples for filtering
                        }
                    ))
                
                total_tables += 1

            # 3. Batch Upsert
            if points:
                try:
                    qdrant_client.upsert(
                        collection_name=settings.DB_COLLECTION_NAME,
                        points=points
                    )
                    total_points += len(points)
                    logger.info(f"✅ Ingested {len(batch)} tables ({len(points)} total nodes).")
                except Exception as e:
                    logger.error(f"❌ Batch upsert failed: {e}")

        logger.info(f"🎉 Ingestion Finished. Tables: {total_tables}, Total Nodes: {total_points}")