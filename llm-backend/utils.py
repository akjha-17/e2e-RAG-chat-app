from typing import Generator
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