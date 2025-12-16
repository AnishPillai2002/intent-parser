# Embedding logic
from sentence_transformers import SentenceTransformer
from app.schemas.schemas import SQLIntentPoint
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))


model = SentenceTransformer(MODEL_NAME)

def embed_text(text: str) -> list[float]:
    return model.encode(text).tolist()


def flatten_intent(intent: dict) -> str:
    return " ".join(
        [intent["text"]] +
        intent["examples"] +
        intent["sql_syntax"]
    )

def flatten_intent_payload(intent: SQLIntentPoint) -> str:
    return " ".join(
        [intent.description] +
        intent.examples +
        intent.sql_syntax
    )