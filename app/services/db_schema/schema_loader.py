import uuid
import itertools
from typing import Dict, Iterable, List
from qdrant_client.models import PointStruct, VectorParams, Distance, PayloadSchemaType

# Project Imports
from app.config import settings
from app.vectorstore.qdrant_client import client as qdrant_client
from app.services.db_schema.schema_extractor import SchemaExtractor 
from app.services.embedding.embedding import embedding_service  # <--- Use your singleton!
from app.utils.logging_util import logger 

class SchemaIngestionService:
    def __init__(self):
        """
        Initialize the service resources that are SHARED across requests.
        We do NOT initialize the extractor here because the DB URL changes per request.
        """
        # 1. Use the Singleton Embedding Service (Lazy Loaded)
        self.embedding_service = embedding_service
        
        # 2. Use the Singleton Qdrant Client
        self.client = qdrant_client
        
        self.batch_size = 25 
        
        # 3. Ensure Collection exists on startup (Safe to call multiple times)
        self._ensure_collection(settings.DB_COLLECTION_NAME)

    def _ensure_collection(self, collection_name: str):
        """Ensures collection exists and ALL required payload indexes are present."""
        try:
            collections = self.client.get_collections()
            existing_names = {c.name for c in collections.collections}

            if collection_name not in existing_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=settings.VECTOR_SIZE, distance=Distance.COSINE),
                )

            # Create keyword indexes for efficient filtering during retrieval
            for field in ["type", "table_name"]:
                self.client.create_payload_index(
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
        """Contextualized text for the Column-level node."""
        text = f"Table: {table_name}, Column: {column['name']} (Type: {column['type']})"
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

    # ---------------------------------------------------------
    # PUBLIC METHOD: Accepts db_url dynamically
    # ---------------------------------------------------------
    def run_ingestion(self, db_url: str) -> int:
        """
        Main entry point: Extract -> Contextualize -> Embed -> Upsert
        
        Args:
            db_url (str): The dynamic database connection string for this request.
        """
        logger.info("🚀 Starting Advanced Hierarchical Ingestion...")
        
        # 1. Instantiate the Extractor specifically for THIS request
        #    This ensures we connect to the correct dynamic DB.
        extractor = SchemaExtractor(db_url=db_url)
        
        table_generator = extractor.extract_schema_generator()
        total_tables = 0
        total_points = 0

        # 2. Process in batches
        for batch in self._batch_iterator(table_generator, self.batch_size):
            points = []
            
            # --- PRE-CALCULATE TEXTS FOR BATCH EMBEDDING ---
            # To optimize performance, we gather all texts first and embed them in one go
            # rather than calling .encode() one by one inside the loop.
            texts_to_embed = []
            metadata_map = [] # Keeps track of what each text belongs to
            
            for table in batch:
                # Prepare Table Text
                t_text = self._generate_table_text(table)
                texts_to_embed.append(t_text)
                metadata_map.append({"type": "table", "data": table})
                
                # Prepare Column Texts
                for col in table['columns']:
                    c_text = self._generate_column_text(table['table_name'], col)
                    texts_to_embed.append(c_text)
                    metadata_map.append({"type": "column", "data": col, "parent_table": table['table_name']})

            # --- BATCH EMBEDDING CALL ---
            vectors = self.embedding_service.batch_embed(texts_to_embed)
            
            # --- CONSTRUCT POINTS ---
            for i, vector in enumerate(vectors):
                meta = metadata_map[i]
                
                if meta["type"] == "table":
                    table = meta["data"]
                    t_name = table['table_name']
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tbl_{t_name}"))
                    
                    points.append(PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "type": "table",
                            "table_name": t_name,
                            "schema_text": texts_to_embed[i],
                            "full_schema": table 
                        }
                    ))
                    total_tables += 1
                    
                elif meta["type"] == "column":
                    col = meta["data"]
                    t_name = meta["parent_table"]
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"col_{t_name}_{col['name']}"))
                    parent_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"tbl_{t_name}"))
                    
                    points.append(PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "type": "column",
                            "table_name": t_name,
                            "column_name": col['name'],
                            "context_text": texts_to_embed[i],
                            "parent_table_id": parent_id,
                            "samples": col.get('samples', [])
                        }
                    ))

            # --- UPSERT ---
            if points:
                try:
                    self.client.upsert(
                        collection_name=settings.DB_COLLECTION_NAME,
                        points=points
                    )
                    total_points += len(points)
                    logger.info(f"✅ Batch upserted: {len(points)} nodes.")
                except Exception as e:
                    logger.error(f"❌ Batch upsert failed: {e}")

        logger.info(f"🎉 Ingestion Finished. Tables: {total_tables}, Total Nodes: {total_points}")
        return total_tables

# ---------------------------------------------------------
# SINGLETON INSTANCE
# ---------------------------------------------------------
schema_ingestion_service = SchemaIngestionService()