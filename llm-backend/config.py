# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR  = BASE_DIR / "data"
# allow overriding via FAISS_PERSIST_DIR env var (absolute or relative)
INDEX_DIR = Path(os.getenv("FAISS_PERSIST_DIR", str(BASE_DIR / "db/faiss"))).resolve()

# Embeddings
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "hf")  # "hf" | "openai"
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/distiluse-base-multilingual-cased-v1")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# Chunking
CHUNK_WORDS = int(os.getenv("CHUNK_WORDS", "450"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))

# Retrieval
TOP_K_DEFAULT = int(os.getenv("TOP_K_DEFAULT", "4")) 

# LLM generator backend
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")   # "openai" | "ollama" | "hf" | "none"

# OpenAI config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Ollama config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# HuggingFace local text-generation (optional)
HF_MODEL = os.getenv("HF_MODEL", "microsoft/phi-3-mini-4k-instruct")
HF_MAX_NEW_TOKENS = int(os.getenv("HF_MAX_NEW_TOKENS", "512"))
HF_TEMPERATURE = float(os.getenv("HF_TEMPERATURE", "0.2"))

# Upload limits
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 20 * 1024 * 1024))  # 20 MB
ALLOWED_EXTENSIONS = set(x.strip().lower() for x in os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,doc,pptx,ppt,txt,md,xlsx").split(","))

# Auth / OAuth
AZURE_TENANT = os.getenv("AZURE_TENANT", "")  # if set, enable Azure AD JWKS validation
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")  # audience to check in tokens
AZURE_OPENID_CONFIG = f"https://login.microsoftonline.com/{AZURE_TENANT}/v2.0/.well-known/openid-configuration" if AZURE_TENANT else None
JWKS_CACHE_TTL = int(os.getenv("JWKS_CACHE_TTL", 3600))

# Local dev JWT fallback (HS256). 
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")

# Misc
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

#Vector Store
VECTOR_STORE = os.getenv("VECTOR_STORE", "faiss")  # "faiss" or "pinecone"

#Pinecone settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "documents-index")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")

