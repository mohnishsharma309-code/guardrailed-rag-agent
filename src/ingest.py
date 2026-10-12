"""Chunk markdown docs, embed, and load into ChromaDB."""
import os

from .config import settings
from .embeddings import get_embed_fn
from .vectorstore import DocStore


def chunk_markdown(text: str, chunk_size: int = 600, overlap: int = 120):
    """Split on paragraph boundaries; hard-split oversized paragraphs."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        candidate = (cur + "\n\n" + p).strip() if cur else p
        if len(candidate) <= chunk_size:
            cur = candidate
        else:
            if cur:
                chunks.append(cur)
            cur = (cur[-overlap:] + "\n\n" + p).strip() if cur else p
            while len(cur) > chunk_size:
                chunks.append(cur[:chunk_size])
                cur = cur[chunk_size - overlap :]
    if cur:
        chunks.append(cur)
    return chunks


def ingest(docs_dir: str = None, reset: bool = False) -> int:
    docs_dir = docs_dir or settings.docs_dir
    store = DocStore(settings.chroma_dir, settings.collection_name, get_embed_fn())
    if reset:
        store.reset(settings.collection_name)

    ids, texts, metadatas = [], [], []
    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".md"):
            continue
        slug = fname[: -len(".md")]
        with open(os.path.join(docs_dir, fname), encoding="utf-8") as f:
            text = f.read()
        for i, chunk in enumerate(
            chunk_markdown(text, settings.chunk_size, settings.chunk_overlap)
        ):
            ids.append(f"{slug}#{i}")
            texts.append(chunk)
            metadatas.append({"source": fname, "chunk_index": i})

    if ids:
        store.add(ids, texts, metadatas)
    return len(ids)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="wipe the collection first")
    args = ap.parse_args()
    n = ingest(reset=args.reset)
    print(f"Ingested {n} chunks.")
