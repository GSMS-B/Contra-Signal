import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings
from backend.config import GEMINI_API_KEY

# Configure GenAI
genai.configure(api_key=GEMINI_API_KEY)

class GoogleGenerativeAIEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        import time
        t_start = time.time()
        model = "models/text-embedding-004"
        title = "Financial Report Context"
        
        embeddings = []
        batch_size = 100
        print(f"[GoogleEmbeddings] Embedding {len(input)} chunks (Batch Size: {batch_size})...")
        
        for i in range(0, len(input), batch_size):
            batch = input[i:i+batch_size]
            print(f"[GoogleEmbeddings] Processing batch {i//batch_size + 1}/{(len(input)-1)//batch_size + 1} (Indices {i}-{i+len(batch)})...")
            try:
                # API Call (1 call for up to 100 chunks)
                # Note: content accepts a list of strings
                response = genai.embed_content(
                    model=model,
                    content=batch,
                    task_type="retrieval_document",
                    title=title
                )
                
                # Response 'embedding' is a list of lists for batch input
                batch_embeddings = response['embedding']
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"[GoogleEmbeddings] Error in batch {i}: {e}")
                # Fallback: fill with zeros to match length
                embeddings.extend([[0.0]*768 for _ in range(len(batch))])

        print(f"[GoogleEmbeddings] Finished embedding {len(input)} chunks in {time.time() - t_start:.2f}s.")
        return embeddings

class FinancialRAG:
    def __init__(self, persist_dir: str = "chroma_db"):
        self.persist_dir = persist_dir
        
        # Use Google Embeddings (Server-side) instead of local SentenceTransformers (CPU-bound)
        self.embedding_fn = GoogleGenerativeAIEmbeddingFunction()

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
        n_found = len(results['documents'][0])
        print(f"[RAG] Query: '{question}' for '{company_name}' -> Found {n_found} docs.")
        if n_found == 0:
            return ""
        
        docs = results['documents'][0]
        return "\n\n---\n\n".join(docs)
    
    def clear_company(self, company_name: str):
        # Basic cleanup if needed, Chroma support for delete with where clause
        try:
            self.collection.delete(where={"company": company_name})
        except:
            pass
