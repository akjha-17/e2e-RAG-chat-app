# store.py (replace your existing file with this revised version)
import os
import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from embeddings import load_embeddings,get_EmbeddingModelDimention
from loaders import load_text_from_file
from utils import chunk_texts
from FlagEmbedding import FlagReranker
from config import INDEX_DIR, CHUNK_WORDS, CHUNK_OVERLAP, EMBED_MODEL, EMBED_BACKEND, OPENAI_EMBED_MODEL, PINECONE_CLOUD, TOP_K_DEFAULT, PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, VECTOR_STORE, RERANKER_MODEL

# Import pinecone only if needed to avoid errors when not configured
if VECTOR_STORE == "pinecone":
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError:
        print("Warning: Pinecone not available but VECTOR_STORE is set to pinecone")

# Import filelock for FAISS
try:
    from filelock import FileLock
except ImportError:
    # Fallback dummy FileLock if filelock is not available
    class FileLock:
        def __init__(self, path): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass

import logging
import uuid
import time

logger = logging.getLogger(__name__)

#INDEX_PATH = INDEX_DIR / "vectors.faiss"
META_PATH  = INDEX_DIR / "metadata.json"
#EMB_PATH   = INDEX_DIR / "embed_info.json"
LOCK_PATH  = INDEX_DIR / ".lock"

class VectorStore:
    def __init__(self):
        self._embed_fn = None
        self.index: Optional[faiss.Index] = None
        self.meta: List[Dict] = []
        self.reranker = FlagReranker(RERANKER_MODEL, use_fp16=True, query_lang_detect=True)
        
        # Initialize lock for FAISS operations
        self._lock = FileLock(str(LOCK_PATH) + ".lock")
        
        # Initialize Pinecone only if configured and API key is provided
        if VECTOR_STORE == "pinecone":
            if not PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY is required when using Pinecone vector store")
            
            try:
                self.pc = Pinecone(api_key=PINECONE_API_KEY)
                self.index_name = PINECONE_INDEX
                existing_indexes = self.pc.list_indexes()
                existing_index_names = [idx["name"] for idx in existing_indexes]  # extract names
                if self.index_name not in existing_index_names:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=get_EmbeddingModelDimention(),  # Call the function
                        metric="cosine", 
                        spec=ServerlessSpec(
                            cloud=PINECONE_CLOUD,  # or your cloud provider
                            region=PINECONE_ENV
                        )
                    )
                self.index = self.pc.Index(self.index_name)
            except Exception as e:
                print(f"Warning: Failed to initialize Pinecone: {e}")
                raise
        
        elif VECTOR_STORE == "faiss":
            # Ensure FAISS directory exists
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            # Load existing FAISS index if available
            self._load_or_init_index()

    def _load_embedder(self):
        if self._embed_fn is None:
            self._embed_fn = load_embeddings()

    def _index_path_for_model(self):
        current_model = EMBED_MODEL if EMBED_BACKEND == "hf" else OPENAI_EMBED_MODEL
        safe_model = current_model.replace("/", "_")
        return INDEX_DIR / f"index_{EMBED_BACKEND}_{safe_model}.faiss"

    def _save_all(self):
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self.index is not None:
                # Check if index has any vectors before trying to save
                if hasattr(self.index, 'ntotal') and self.index.ntotal > 0:
                    path = self._index_path_for_model()
                    try:
                        # Ensure parent directory exists
                        path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Use FAISS write_index instead of serialize_index
                        faiss.write_index(self.index, str(path))
                        print(f"[SAVE] Successfully saved FAISS index with {self.index.ntotal} vectors to {path}")
                    except Exception as e:
                        print(f"[ERROR] Failed to save FAISS index: {str(e)}")
                        logger.error("Failed to save FAISS index: %s", str(e))
                        import traceback
                        traceback.print_exc()
                        # Don't raise the exception, just log it so the metadata can still be saved
                else:
                    print("[SAVE] Skipping save - FAISS index is empty")

            # Save metadata
            try:
                META_PATH.write_text(json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"[SAVE] Saved metadata for {len(self.meta)} chunks")
            except Exception as e:
                print(f"[ERROR] Failed to save metadata: {str(e)}")
                logger.error("Failed to save metadata: %s", str(e))

    def _load_or_init_index(self):
        with self._lock:
            path = self._index_path_for_model()
            if path.exists() and META_PATH.exists():
                try:
                    print(f"[LOAD] Loading FAISS index from: {path}")
                    # Use FAISS read_index instead of deserialize_index
                    self.index = faiss.read_index(str(path))
                    print(f"[LOAD] Successfully loaded FAISS index with {self.index.ntotal} vectors")
                    logger.info("Loaded FAISS index: %s", path)
                except Exception as e:
                    print(f"[ERROR] Failed to load FAISS index: {str(e)}")
                    logger.error("Failed to load FAISS index: %s", e)
                    self.index = None

                try:
                    self.meta = json.loads(META_PATH.read_text(encoding="utf-8"))
                    print(f"[LOAD] Loaded metadata for {len(self.meta)} chunks")
                except Exception as e:
                    print(f"[ERROR] Failed to load metadata: {str(e)}")
                    self.meta = []
                return

            # nothing to load
            print("[LOAD] No existing index found, initializing empty")
            self.index = None
            self.meta = []



    def _embed(self, texts: List[str], is_query: bool=False) -> np.ndarray:
        self._load_embedder()
        return self._embed_fn(texts, is_query=is_query)

    def _add_vectors(self, vectors: np.ndarray, documents: List[any]=None):
        if VECTOR_STORE == "faiss":
             self._add_vectors_faiss(vectors)
        elif VECTOR_STORE == "pinecone":
             self._add_vectors_pinecone(vectors, documents)

    def _add_vectors_faiss(self, vectors: np.ndarray):
        print(f"[ADD_VECTORS] Adding {vectors.shape[0]} vectors of dimension {vectors.shape[1]}")
        print(f"[ADD_VECTORS] Vector dtype: {vectors.dtype}, shape: {vectors.shape}")
        
        if vectors.shape[0] == 0:
            print("[ADD_VECTORS] Warning: No vectors to add, skipping")
            return
            
        # Ensure vectors are float32 (required by FAISS)
        if vectors.dtype != np.float32:
            print(f"[ADD_VECTORS] Converting vectors from {vectors.dtype} to float32")
            vectors = vectors.astype(np.float32)
        
        # Ensure vectors are C-contiguous for FAISS
        if not vectors.flags['C_CONTIGUOUS']:
            print("[ADD_VECTORS] Converting vectors to C-contiguous array")
            vectors = np.ascontiguousarray(vectors)
            
        if self.index is None:
            dim = vectors.shape[1]
            print(f"[ADD_VECTORS] Creating new FAISS index with dimension {dim}")
            self.index = faiss.IndexFlatL2(dim)
        
        print(f"[ADD_VECTORS] Index before adding: {self.index.ntotal} vectors")
        try:
            self.index.add(vectors)
            print(f"[ADD_VECTORS] Index after adding: {self.index.ntotal} vectors")
        except Exception as e:
            print(f"[ERROR] Failed to add vectors to FAISS index: {str(e)}")
            logger.error("Failed to add vectors to FAISS index: %s", str(e))
            raise
    
    def _add_vectors_pinecone(self, embeddings: np.ndarray, documents: List[any]):
        vectors=[]

        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            metadata=dict(doc.metadata) if hasattr(doc, 'metadata') else {}
            metadata['doc_index']=i
            metadata['content_length']=len(doc.page_content) if hasattr(doc, 'page_content') else len(str(doc))
            # Store the text content in metadata for retrieval (truncated to avoid size limits)
            metadata['text'] = doc.page_content[:1000] if hasattr(doc, 'page_content') else str(doc)[:1000]
            # Ensure source_file is properly set
            metadata['source_file'] = metadata.get('source_file', 'unknown')
            vector = (doc_id, emb, metadata)
            vectors.append(vector)
            print(f"[ADD_VECTORS] Upserting vector number {i} vectors to Pinecone index")
        # Store
        self.index.upsert(vectors)

    def file_already_indexed(self, source_file: str) -> bool:
        """Check if a file with given name has already been indexed."""
        if VECTOR_STORE == "faiss":
            # For FAISS, check if file exists in metadata
            self._load_or_init_index()
            return any(meta.get("file") == source_file for meta in self.meta)
        elif VECTOR_STORE == "pinecone":
            try:
                result = self.index.query(
                    vector=[0.0] * self.index.describe_index_stats()["dimension"],  # Dummy vector for filtering
                    top_k=1,
                    filter={"source_file": {"$eq": source_file}},
                    include_metadata=True,
                    include_values=False,
                )
                return bool(result and result.get("matches"))
            except Exception as e:
                print(f"Error checking if file is indexed: {e}")
                return False
        return False

    def build_from_folder(self, folder: Path) -> int:
        self._load_embedder()
        
        docs = []
        for f in folder.rglob("*"):
            if not f.is_file():
                continue
            # optionally skip very large files
            try:
                if f.stat().st_size > 50 * 1024 * 1024:
                    logger.warning("Skipping large file: %s", f)
                    continue
            except Exception:
                pass
            # load_text_from_file now returns List[Document]
            file_docs = load_text_from_file(str(f))
            docs.extend(file_docs)
        
        if not docs:
            self.index = None
            self.meta = []
            self._save_all()
            return 0
        
        # Chunk all documents
        chunks = chunk_texts(docs, CHUNK_WORDS, CHUNK_OVERLAP)
        
        # Extract text for embedding
        texts = [doc.page_content for doc in chunks]
        vecs = self._embed(texts)
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(vecs.shape[1])
        self.index.add(vecs)
        
        # Create metadata
        metas = []
        for doc in chunks:
            metas.append({
                "file": doc.metadata.get('source_file', 'unknown'),
                "text": doc.page_content[:1000],
                "page_number": doc.metadata.get('page_number', -1),
                "images": []
            })
        
        self.meta = metas
        self._save_all()
        return len(texts)

    def append_files(self, paths: List[str]) -> int:
        # ensure index/meta loaded before append
        if VECTOR_STORE == "faiss":
            self._load_or_init_index()
        
        docs = []
        for path in paths:
            print(f"[APPEND_FILES] Processing file: {path}")
            try:
                file_docs = load_text_from_file(path)
                # Ensure file_docs is always a list
                if not isinstance(file_docs, list):
                    file_docs = [file_docs] if file_docs else []
                print(f"[APPEND_FILES] Loaded {len(file_docs)} documents from {path}")
                docs.extend(file_docs)
            except Exception as e:
                print(f"[APPEND_FILES] Error processing file {path}: {e}")
                continue

        if not docs:
            print("[APPEND_FILES] No documents loaded, returning 0")
            return 0

        print(f"[APPEND_FILES] Total documents before chunking: {len(docs)}")
        chunks = chunk_texts(docs, CHUNK_WORDS, CHUNK_OVERLAP)
        print(f"[APPEND_FILES] Total chunks after splitting: {len(chunks)}")
        
        if VECTOR_STORE == "faiss":
            # For FAISS, we need to handle metadata separately
            chunktexts = [doc.page_content for doc in chunks if hasattr(doc, 'page_content') and doc.page_content.strip()]
            print(f"[APPEND_FILES] Extracted {len(chunktexts)} non-empty text chunks for embedding")
            
            if not chunktexts:
                print("[APPEND_FILES] No text to embed, returning 0")
                return 0
                
            embeddings = self._embed(chunktexts)
            print(f"[APPEND_FILES] Generated embeddings shape: {embeddings.shape}")
            self._add_vectors(embeddings)
            
            # Add metadata for each chunk
            for doc in chunks:
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    self.meta.append({
                        "file": doc.metadata.get('source_file', 'unknown'),
                        "text": doc.page_content[:1000],
                        "page_number": doc.metadata.get('page_number', -1),
                        "images": []  # Placeholder for images
                    })
            
            # Save the updated index and metadata
            self._save_all()
            
        elif VECTOR_STORE == "pinecone":
            chunktexts = [doc.page_content for doc in chunks if hasattr(doc, 'page_content')]
            if chunktexts:
                embeddings = self._embed(chunktexts)
                self._add_vectors(embeddings, chunks)
            
            # Delete files after processing for Pinecone
            for path in paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"[APPEND_FILES] Warning: Could not delete file {path}: {e}")
        
        return len(chunks)

    def search(self, query: str, k: int = TOP_K_DEFAULT) -> tuple[List[Dict], Dict]:
        print("[SEARCH] using vector store:", VECTOR_STORE)
        if VECTOR_STORE == "faiss":
            results, timings = self.search_faiss(query, k)
        elif VECTOR_STORE == "pinecone":
            results, timings = self.search_pinecone(query, top_k=k)
        else:
            results = []
            timings = {}
        if results:
            logger.info("Search found %d results (embed: %.2fms, search: %.2fms)", len(results), timings.get("embedding_ms", 0.0), timings.get("vector_search_ms", 0.0))
        else:
            logger.info("Search found no results (embed: %.2fms)", timings.get("embedding_ms", 0.0))
        return results, timings

    def search_faiss(self, query: str, k: int = TOP_K_DEFAULT) -> tuple[List[Dict], Dict]:
        """
        Search for similar text chunks and return results with timing data.
        
        Returns:
            tuple: (results, timings) where timings contains embedding_ms and faiss_search_ms
        """
        
        timings = {}
        
        # if no persisted index, return empty
        if not self._index_path_for_model().exists() and self.index is None:
            return [], {"embedding_ms": 0.0, "vector_search_ms": 0.0}
        if self.index is None:
            self._load_or_init_index()
        
        # Check if index is still None or empty after loading
        if self.index is None:
            return [], {"embedding_ms": 0.0, "vector_search_ms": 0.0}
        
        # Step 1: Embed query (measure embedding model performance)
        start_time = time.perf_counter()
        q_vec = self._embed([query])
        timings["embedding_ms"] = round((time.perf_counter() - start_time) * 1000, 4)  # 4 decimal precision
        
        # ensure k <= number of vectors
        try:
            total_vectors = self.index.ntotal if hasattr(self.index, 'ntotal') else 0
            K = min(k, total_vectors)
        except Exception:
            K = k
        if K == 0:
            return [], timings
        
        # Step 2: Vector search (measure vector store performance)
        start_time = time.perf_counter()
        D, I = self.index.search(q_vec, K)
        timings["vector_search_ms"] = round((time.perf_counter() - start_time) * 1000, 4)  # 4 decimal precision
        
        # Extract scores for normalization
        scores = [float(score) for score in D[0] if score != -1]
        
        # Calculate normalized scores
        if len(scores) > 1:
            min_score = min(scores)
            max_score = max(scores)
            
            def normalize_score(score):
                # Custom linear scale mapping distance [0.0, 1.0] to similarity [0.95, 0.7]
                # You can tune min_d and max_d as needed
                min_d = 1.0   # distance = 1.0 → similarity = 0.95 (95% upper bound)
                max_d = 1.9   # distance = 2.0 → similarity = 0.6 (60% lower bound)
                
                if score <= min_d:
                    return 0.95
                if score >= max_d:
                    return 0.6
                
                # Linear interpolation
                return 0.95 - (score - min_d) * (0.25 / (max_d - min_d))
        else:
            # If only one result, give it a perfect score
            def normalize_score(score):
                return 1.0
        
        out = []
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
                continue
            meta = self.meta[idx] if idx < len(self.meta) else {}
            raw_score = float(score)
            normalized_score = normalize_score(raw_score)
            
            out.append({
                **meta,
                "score": raw_score, 
                "score_normalized": normalized_score,
                "chunk_id": str(idx),
                "page_number": meta.get("page_number", -1)  # Ensure page_number is included
            })
        return out, timings

    def summarize_kb(self):
        stats = self.index.describe_index_stats()
        # Example pseudo-code
        return f"""
        Knowledge base contains documents,
        primarily from domains: {', '.join(stats['namespaces'].keys())}.
        Each document is chunked and indexed for multilingual retrieval.
        """

    def search_pinecone(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> tuple[List[dict], dict]:
        # Returns top_k documents and their similarity scores
        timings = {}
        start_time = time.perf_counter()
        query_embedding = self._embed(query, is_query=True)
        timings["embedding_ms"] = round((time.perf_counter() - start_time) * 1000, 4)
        vector_search_start = time.perf_counter()
        query_response = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
        timings["vector_search_ms"] = round((time.perf_counter() - vector_search_start) * 1000, 4)
        
        matches = query_response.get("matches", [])

        if not matches:
            timings["rerank_ms"] = 0.0
            timings["total_ms"] = timings["embedding_ms"] + timings["vector_search_ms"]
            return [], timings
        
        retrieved_docs = []
        for match in matches:
            metadata = match.get('metadata', {})
            similarity = match['score']  # Pinecone returns cosine similarity by default
            #normalized_score = match['score']
            
            retrieved_docs.append({
                'chunk_id': match['id'],
                'text': metadata.get('text', ''),
                'file': metadata.get('source_file', ''),
                'page_number': metadata.get('page_number', -1),
                'score': similarity,  # Keep original cosine similarity
                "score_normalized": similarity  # Normalized for display
            })

        # 🔹 Step 3: Apply reranking
        rerank_start = time.perf_counter()
        # Prepare (query, doc) pairs
        pairs = [(query, doc["text"]) for doc in retrieved_docs]

        # Predict rerank scores
        rerank_scores = np.array(self.reranker.compute_score(pairs))
        #normalized=(x−min(x)​)/(max(x)−min(x))
        normalized_scores = (rerank_scores - rerank_scores.min()) / (rerank_scores.max() - rerank_scores.min() + 1e-9)
        combined_scores = 0.5*normalized_scores + 0.5*np.array([doc['score'] for doc in retrieved_docs])

        # Attach reranker scores
        for doc, rscore in zip(retrieved_docs, combined_scores):
            doc["score_normalized"] = float(rscore)
        
        timings["rerank_ms"] = round((time.perf_counter() - rerank_start) * 1000, 4)

        # Sort by score_normalized (descending)
        retrieved_docs = sorted(retrieved_docs, key=lambda x: x["score_normalized"], reverse=True)
        print(f"[SEARCH] Reranked top {len(retrieved_docs)} documents")

        timings["total_ms"] = round((time.perf_counter() - start_time) * 1000, 4)
        return retrieved_docs, timings

store = VectorStore()
