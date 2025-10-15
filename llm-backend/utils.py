from typing import Dict, Generator
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import langid

def detect_language(text: str) -> str:
    try:
        lang, _ = langid.classify(text)
        return lang
    except Exception:
        return "en"

def chunk_texts(documents: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    """Split texts into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len
    )
    # If not using LangChain Document class directly, you can wrap similarly
    chunks = splitter.split_documents(documents)
    return chunks

def build_context(docs: List[Dict], max_tokens: int = 2000) -> str:
    """Join top reranked chunks into a clean context."""
    context = ""
    for doc in docs:
        if len(context.split()) > max_tokens:
            break
        context += f"\n\n[Source: {doc.get('source_file','Unknown')}, Page {doc.get('page_number', -1)}] {doc.get('text','')}"
    return context.strip()