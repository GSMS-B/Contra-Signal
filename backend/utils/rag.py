import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

class FinancialRAG:
    def __init__(self, persist_dir: str = "chroma_db"):
        self.persist_dir = persist_dir
        # Initialize Client
        # Note: Chroma new version uses PersistentClient
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        self.collection = self.client.get_or_create_collection(name="financial_reports")
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
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

    def query_context(self, question: str, company_name: str, n_results: int = 5) -> str:
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where={"company": company_name}
        )
        
        docs = results['documents'][0]
        return "\n\n---\n\n".join(docs)
    
    def clear_company(self, company_name: str):
        # Basic cleanup if needed, Chroma support for delete with where clause
        try:
            self.collection.delete(where={"company": company_name})
        except:
            pass
