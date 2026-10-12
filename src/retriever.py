"""Top-k semantic search over ingested docs."""
from .config import settings
from .embeddings import get_embed_fn
from .vectorstore import DocStore


class Retriever:
    def __init__(self, store: DocStore = None):
        self.store = store or DocStore(
            settings.chroma_dir, settings.collection_name, get_embed_fn()
        )

    def search(self, query: str, top_k: int = None):
        top_k = top_k or settings.top_k
        hits = self.store.query(query, top_k)
        return [
            {
                "id": h["id"],
                "text": h["text"],
                "source": h["metadata"].get("source", "unknown"),
                "score": 1.0 - float(h["distance"]),
            }
            for h in hits
        ]

    def read_chunk(self, chunk_id: str):
        return self.store.get(chunk_id)
