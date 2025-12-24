# Qdrant connection + helpers
from qdrant_client import QdrantClient
from app.config import settings
from qdrant_client.models import VectorParams, Distance


client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

def ensure_collection():
    collections = client.get_collections().collections
    if settings.COLLECTION_NAME not in [c.name for c in collections]:
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=settings.VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )