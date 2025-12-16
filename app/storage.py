# Store intents in Qdrant
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.qdrant_client import client, COLLECTION_NAME
from app.embeddings import flatten_intent,flatten_intent_payload, embed_text
from app.sql_intents import SQL_INTENTS
from typing import List
from qdrant_client.models import PointStruct
from app.embeddings import embed_text
from app.qdrant_client import client, COLLECTION_NAME
from app.schemas.schemas import SQLIntentPoint


def store_dynamic_intents(intents: List[SQLIntentPoint]):
    points = []

    for intent in intents:
        vector = embed_text(flatten_intent_payload(intent))

        points.append(
            PointStruct(
                id=intent.id,
                vector=vector,
                payload={
                    "operation": intent.operation,
                    "category": intent.category,
                    "description": intent.description,
                    "examples": intent.examples,
                    "sql_syntax": intent.sql_syntax
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)


def store_sql_intents():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

    points = []

    for intent in SQL_INTENTS:
        vector = embed_text(flatten_intent(intent))
        points.append(
            PointStruct(
                id=intent["id"],
                vector=vector,
                payload={
                    "operation": intent["operation"],
                    "category": intent["category"],
                    "description": intent["text"],
                    "examples": intent["examples"],
                    "sql_syntax": intent["sql_syntax"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)

