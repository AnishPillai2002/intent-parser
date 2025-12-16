# Qdrant connection
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sample_collection")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
