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
        def _emb(texts: List[str]) -> np.ndarray:
            return np.asarray(model.encode(texts, convert_to_numpy=True), dtype="float32")
        return _emb

    elif EMBED_BACKEND == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set for OpenAI embeddings.")
        # prefer the official OpenAI client if available - small wrapper
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            def _emb(texts: List[str]) -> np.ndarray:
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
    if EMBED_MODEL == "sentence-transformers/distiluse-base-multilingual-cased-v1":
        return 512
    elif EMBED_MODEL == "text-embedding-3-small":
        return 384
    else:
        return 512  # default to 512