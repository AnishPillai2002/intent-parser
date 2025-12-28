from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.text_normalizer import normalize
from app.utils.logging_util import logger

class EmbeddingService:
    """
    Singleton service to handle text embeddings.
    Implements Lazy Loading to ensure fast server startup.
    """
    _instance = None

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._model = None  # Model is initially None

    @property
    def model(self):
        """Lazy load the model only when accessed."""
        if self._model is None:
            logger.info(f"⏳ Loading embedding model: {self.model_name}...")
            try:
                self._model = SentenceTransformer(self.model_name)
                logger.info("✅ Embedding model loaded successfully.")
            except Exception as e:
                logger.critical(f"❌ Failed to load embedding model: {e}")
                raise e
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single string."""
        clean_text = normalize(text)
        return self.model.encode(clean_text).tolist()

    def batch_embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates embeddings for a list of strings."""
        if not texts:
            return []
            
        clean_texts = [normalize(t) for t in texts]
        
        # Ensure batch_size is safe
        safe_batch_size = min(len(clean_texts), batch_size)
        
        return self.model.encode(clean_texts, batch_size=safe_batch_size).tolist()

# ---------------------------------------------------------
# SINGLETON INSTANCE
# ---------------------------------------------------------
# Import this instance elsewhere, do not instantiate the class manually.
embedding_service = EmbeddingService()