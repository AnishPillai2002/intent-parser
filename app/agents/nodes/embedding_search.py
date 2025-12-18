from app.embeddings.embedder import embed_text
from app.vectorstore.qdrant_client import client
from app.config import COLLECTION_NAME

def embedding_search_node(state):
    vector = embed_text(state["query"])
    hits = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=10,
        query_filter={
            "must": [
                {
                    "key": "operation",
                    "match": {"any": state["allowed_operations"]}
                }
            ]
        }
    )
    state["vector_hits"] = hits
    return state
