import os
import json
import math
import logging
from app.database import SessionLocal
from app.models import RAGChunk
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, llm_service=None):
        if llm_service is None:
            self.llm_service = LLMService()
        else:
            self.llm_service = llm_service
        self.is_indexed = True  # We have our DB store ready

    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> list:
        """
        Split text into word-based chunks with overlap.
        """
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        # Word-based sliding window chunking
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words).strip()
            if chunk:
                chunks.append(chunk)
            i += (chunk_size - overlap)
            if i >= len(words) or (chunk_size - overlap) <= 0:
                break
                
        return chunks

    def ingest_document(self, db, role: str, document_name: str, doc_text: str):
        """
        Splits doc_text into chunks, generates embedding vectors using LLMService,
        and saves them to the SQLite database (RAGChunk table).
        """
        logger.info(f"Ingesting document '{document_name}' for role '{role}'")
        chunks = self.chunk_text(doc_text, chunk_size=300, overlap=50)
        
        # Clear existing chunks for this role/document
        db.query(RAGChunk).filter(
            RAGChunk.role == role,
            RAGChunk.document_name == document_name
        ).delete()
        db.commit()

        for chunk_text in chunks:
            embedding = self.llm_service.get_embedding(chunk_text)
            embedding_json = json.dumps(embedding)
            
            chunk_obj = RAGChunk(
                role=role,
                document_name=document_name,
                chunk_text=chunk_text,
                embedding_json=embedding_json
            )
            db.add(chunk_obj)
        
        db.commit()
        logger.info(f"Successfully ingested {len(chunks)} chunks for document '{document_name}' ({role})")

    def retrieve(self, db, role: str, query: str, top_k: int = 3) -> list:
        """
        Cosine similarity search across SQLite RAGChunk records.
        """
        logger.info(f"Retrieving context for query: '{query}' [role: {role}]")
        query_embedding = self.llm_service.get_embedding(query)
        if not query_embedding:
            return []

        # Load all chunks for this role
        db_chunks = db.query(RAGChunk).filter(RAGChunk.role == role).all()
        if not db_chunks:
            logger.warning(f"No indexed RAG chunks found for role '{role}' in database.")
            return []

        results = []
        for chunk in db_chunks:
            try:
                chunk_embedding = json.loads(chunk.embedding_json)
                # Compute cosine similarity
                score = self._cosine_similarity(query_embedding, chunk_embedding)
                results.append({
                    "chunk_id": chunk.id,
                    "document_name": chunk.document_name,
                    "text": chunk.chunk_text,
                    "score": score
                })
            except Exception as e:
                logger.error(f"Error computing similarity for chunk {chunk.id}: {e}")
                continue

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1, vec2) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

    def build_index(self, kb_path: str):
        """
        Scans a directory or file and ingests markdown or text documents into SQLite.
        Used at server startup in main.py.
        """
        db = SessionLocal()
        try:
            if os.path.isdir(kb_path):
                # Iterate over files in the directory
                for filename in os.listdir(kb_path):
                    file_path = os.path.join(kb_path, filename)
                    if os.path.isfile(file_path) and filename.endswith(('.md', '.txt')):
                        # Determine role from filename, e.g. "backend_engineer.md" -> "backend_engineer"
                        name_without_ext = os.path.splitext(filename)[0]
                        role = name_without_ext
                        if role not in ["ai_ml_engineer", "backend_engineer", "data_scientist"]:
                            # Fallback mapping or role based on filename
                            if "ml" in role or "ai" in role:
                                role = "ai_ml_engineer"
                            elif "data" in role or "science" in role:
                                role = "data_scientist"
                            else:
                                role = "backend_engineer"

                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                doc_text = f.read()
                            self.ingest_document(db, role, filename, doc_text)
                        except Exception as e:
                            logger.error(f"Failed to ingest file '{file_path}' during build_index: {e}")
            elif os.path.isfile(kb_path):
                filename = os.path.basename(kb_path)
                name_without_ext = os.path.splitext(filename)[0]
                role = name_without_ext if name_without_ext in ["ai_ml_engineer", "backend_engineer", "data_scientist"] else "backend_engineer"
                with open(kb_path, "r", encoding="utf-8") as f:
                    doc_text = f.read()
                self.ingest_document(db, role, filename, doc_text)
        finally:
            db.close()