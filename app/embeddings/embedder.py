# batch / single embed utils
from app.embeddings.model import model
from app.utils.text_normalizer import normalize

def embed_text(text: str) -> list[float]:
    return model.encode(normalize(text)).tolist()

def batch_embed(texts: list[str]) -> list[list[float]]:
    texts = [normalize(t) for t in texts]
    return model.encode(texts, batch_size=32).tolist()
