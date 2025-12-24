import uuid
import itertools
from typing import Dict,Iterable
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, VectorParams, Distance

# Project Imports
from app.config import settings
from app.vectorstore.qdrant_client import  client as qdrant_client
from app.schema_ingestion.schema_extractor import SchemaExtractor  # <--- Using your class
from app.utils.logging_util import logger  # <--- Using the centralized logger

class SchemaIngestionService:
    def __init__(self, db_url: str = None):
        # Pass the db_url down to the Extractor
        self.extractor = SchemaExtractor(db_url=db_url)
        
        # Load the ML Model
        logger.info("⚙️ Loading Embedding Model: %s", settings.EMBEDDING_MODEL)
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.critical("Failed to load embedding model: %s", e, exc_info=True)
            raise e
        self.batch_size = 50  # Process 50 tables at a time
        # Ensure Qdrant Collection Exists
        self._ensure_collection(settings.COLLECTION_NAME)
        self._ensure_collection(settings.DB_COLLECTION_NAME)
        
    def _ensure_collection(self, collection_name: str):
        """Ensure the given Qdrant collection exists; create if missing."""
        try:
            collections = qdrant_client.get_collections()
            existing_names = {c.name for c in collections.collections}

            if collection_name not in existing_names:
                logger.warning(
                    "Collection '%s' not found. Creating...", collection_name
                )

                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )

                logger.info(
                    "✅ Collection '%s' created successfully.", collection_name
                )
            else:
                logger.debug(
                    "Collection '%s' already exists.", collection_name
                )

        except Exception as e:
            logger.error(
                "Failed to ensure collection '%s': %s",
                collection_name,
                e,
                exc_info=True,
            )
            raise


    def _generate_semantic_text(self, table: Dict) -> str:
        """
        Creates a 'Natural Language' representation optimized for embeddings.
        Focuses on meaningful keywords, ignoring generic types like 'varchar'.
        """
        t_name = table['table_name']
        desc = table.get('description', '')
        
        # 1. Clean Column List (Just names usually work better than types for semantic search)
        col_names = ", ".join([c['name'].replace("_", " ") for c in table['columns']])
        
        # 2. Clean Relationships
        relationships = ", ".join(
            [f"related to {fk['foreign_table']}" for fk in table['foreign_keys']]
        )
        
        # 3. Construct Semantic Block
        # "Table 'users' stores customer data. It contains columns: name, email, id. It is related to orders."
        text = f"Table '{t_name}'"
        if desc:
            text += f". Description: {desc}"
        
        text += f". Contains columns: {col_names}."
        
        if relationships:
            text += f" {relationships}."
            
        return text

    def _batch_iterator(self, iterable: Iterable, size: int):
        """Helper to yield chunks from a generator."""
        it = iter(iterable)
        while True:
            chunk = list(itertools.islice(it, size))
            if not chunk:
                break
            yield chunk

    def run_ingestion(self):
        logger.info("🚀 Starting Scalable Schema Ingestion...")
        
        # 1. Get the Generator
        table_generator = self.extractor.extract_schema_generator()
        
        total_ingested = 0

        # 2. Process in Batches
        for batch in self._batch_iterator(table_generator, self.batch_size):
            points = []
            
            # Vectorize the batch
            for table in batch:
                semantic_text = self._generate_semantic_text(table)
                vector = self.model.encode(semantic_text).tolist()
                
                # Deterministic ID based on table name
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, table['table_name']))
                
                points.append(PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "table_name": table['table_name'],
                        "schema_text": semantic_text, # Store the short semantic text
                        "full_schema": table,         # Store the FULL raw schema for the LLM to read later
                        "column_names": [c['name'] for c in table['columns']] # Good for Keyword Filtering
                    }
                ))

            # Upsert the batch
            if points:
                try:
                    qdrant_client.upsert(
                        collection_name=settings.DB_COLLECTION_NAME,
                        points=points
                    )
                    total_ingested += len(points)
                    logger.info(f"✅ Indexed batch of {len(points)} tables. Total: {total_ingested}")
                except Exception as e:
                    logger.error(f"❌ Failed to upsert batch: {e}")

        logger.info("🎉 Ingestion complete.")