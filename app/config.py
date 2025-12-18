# Settings (env, model, qdrant)
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sql_intents")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))
