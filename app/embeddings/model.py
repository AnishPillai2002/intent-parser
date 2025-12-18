# Embedding model loader
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

model = SentenceTransformer(EMBEDDING_MODEL)
