"""Local embedding model, loaded once and reused."""
from .config import settings

_model = None


def get_embed_fn():
    """Return a function texts -> list of normalized embedding vectors."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)

    def embed(texts):
        return _model.encode(texts, normalize_embeddings=True).tolist()

    return embed
