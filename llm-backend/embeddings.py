# embeddings.py (small changes)
#import pip_system_certs.wrapt_requests
from typing import Callable, List
import numpy as np
from config import EMBED_BACKEND, EMBED_MODEL, OPENAI_EMBED_MODEL, OPENAI_API_KEY
from sentence_transformers import SentenceTransformer
from openai import OpenAI

def load_embeddings() -> Callable[[List[str]], np.ndarray]:
    if EMBED_BACKEND == "hf":
        model = SentenceTransformer(EMBED_MODEL)
        def _emb(texts: List[str], is_query: bool = False) -> np.ndarray:
            """Generate normalized embedding with correct prefix for query/document."""
            # BGE-M3 and other BGE models use different prefixes
            if "bge" in EMBED_MODEL.lower():
                prefix = "Represent this sentence for searching relevant passages: " if is_query else ""
            elif "e5" in EMBED_MODEL.lower():
                prefix = "query: " if is_query else "passage: "
            else:
                prefix = "query: " if is_query else ""
            
            prefixed_texts = texts #[prefix + t for t in texts] if prefix else texts
            print(f"[EMBEDDINGS] Generating embeddings for {len(texts)} texts with prefix '{prefixed_texts}'")
            emb = np.asarray(model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True), dtype="float32")
            print(f"[EMBEDDINGS] Generated embeddings completed")
            return emb
        return _emb

    elif EMBED_BACKEND == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set for OpenAI embeddings.")
        # prefer the official OpenAI client if available - small wrapper
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            def _emb(texts: List[str], is_query: bool = False) -> np.ndarray:
                """Generate normalized embedding with correct prefix for query/document."""
                prefix = "query: " if is_query else "passage: "
                resp = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
                vecs = [d.embedding for d in resp.data]
                return np.asarray(vecs, dtype="float32")
            return _emb
        except Exception:
            # last resort, try the older openai library style
            import openai
            openai.api_key = OPENAI_API_KEY
            def _emb(texts: List[str]) -> np.ndarray:
                resp = openai.Embedding.create(model=OPENAI_EMBED_MODEL, input=texts)
                vecs = [d["embedding"] for d in resp["data"]]
                return np.asarray(vecs, dtype="float32")
            return _emb
    else:
        raise ValueError(f"Unsupported EMBED_BACKEND: {EMBED_BACKEND}")
    

def get_EmbeddingModelDimention() -> int:
    # Check HuggingFace models first
    if EMBED_MODEL == "sentence-transformers/distiluse-base-multilingual-cased-v1":
        return 512
    elif EMBED_MODEL == "BAAI/bge-m3":
        return 1024
    elif EMBED_MODEL == "intfloat/multilingual-e5-large":
        return 1024
    elif EMBED_MODEL == "BAAI/bge-large-en-v1.5":
        return 1024
    # Check OpenAI models
    elif EMBED_BACKEND == "openai":
        if OPENAI_EMBED_MODEL == "text-embedding-3-large":
            return 3072
        elif OPENAI_EMBED_MODEL == "text-embedding-3-small":
            return 1536
        else:
            return 1536  # default OpenAI dimension
    else:
        # Default fallback for unknown models
        return 512