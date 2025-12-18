# Qdrant connection + helpers
from qdrant_client import QdrantClient
from app.config import QDRANT_URL, QDRANT_API_KEY,COLLECTION_NAME, VECTOR_SIZE
from qdrant_client.models import VectorParams, Distance


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def ensure_collection():
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )