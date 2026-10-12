"""Thin ChromaDB wrapper — all vector DB calls live here."""
import chromadb


class DocStore:
    def __init__(self, path: str, collection_name: str, embed_fn):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embed_fn = embed_fn

    def add(self, ids, texts, metadatas) -> None:
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=self.embed_fn(texts),
        )

    def query(self, text: str, top_k: int):
        res = self.collection.query(
            query_embeddings=self.embed_fn([text]), n_results=top_k
        )
        out = []
        for i in range(len(res["ids"][0])):
            out.append(
                {
                    "id": res["ids"][0][i],
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i] or {},
                    "distance": res["distances"][0][i],
                }
            )
        return out

    def get(self, chunk_id: str):
        res = self.collection.get(ids=[chunk_id])
        if not res["ids"]:
            return None
        return {
            "id": res["ids"][0],
            "text": res["documents"][0],
            "metadata": res["metadatas"][0] or {},
        }

    def count(self) -> int:
        return self.collection.count()

    def reset(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=collection_name)
