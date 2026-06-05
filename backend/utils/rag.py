import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions
from backend.config import HF_TOKEN

class FinancialRAG:
    def __init__(self, persist_dir: str = "chroma_db"):
        self.persist_dir = persist_dir
        
        # Use HuggingFace all-MiniLM-L6-v2 locally via sentence-transformers (Much faster on CPU)
        print("[RAG] Initializing Local HuggingFace Embedding Model (all-MiniLM-L6-v2)...")
        # Ensure HF_TOKEN is used if provided, otherwise it will download anonymously
        if HF_TOKEN:
            os.environ["HF_TOKEN"] = HF_TOKEN
            
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Initialize Client
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        self.collection = self.client.get_or_create_collection(
            name="financial_reports",
            embedding_function=self.embedding_fn
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )

    def add_document(self, text: str, company_name: str, report_type: str, doc_id: str):
        chunks = self.text_splitter.split_text(text)
        
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{
            "company": company_name,
            "report_type": report_type,
            "doc_id": doc_id,
            "chunk_index": i
        } for i in range(len(chunks))]
        
        print(f"[RAG] Adding {len(chunks)} chunks to Vector DB...")
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print("[RAG] Chunks added successfully.")

    def query_context(self, question: str, company_name: str, n_results: int = 5) -> str:
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where={"company": company_name}
        )
        n_found = len(results['documents'][0]) if results['documents'] else 0
        print(f"[RAG] Query: '{question}' for '{company_name}' -> Found {n_found} docs.")
        if n_found == 0:
            return ""
        
        docs = results['documents'][0]
        return "\n\n---\n\n".join(docs)
    
    def clear_company(self, company_name: str):
        # Basic cleanup if needed
        try:
            self.collection.delete(where={"company": company_name})
        except:
            pass

_rag_instance = None

def get_rag() -> FinancialRAG:
    """Returns a singleton instance of the FinancialRAG."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = FinancialRAG()
    return _rag_instance
