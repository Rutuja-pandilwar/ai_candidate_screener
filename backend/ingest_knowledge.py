import os
import sys
import logging

# Ensure backend root is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models import RAGChunk
from app.services.llm_service import LLMService
from app.rag.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest_knowledge")

def main():
    logger.info("Initializing DB and generating schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    llm_service = LLMService()
    rag_service = RAGService(llm_service)
    
    # Roles and corresponding file paths
    # We will search for files in backend/knowledge_base
    kb_dir = settings.KNOWLEDGE_BASE_DIR
    if not os.path.exists(kb_dir):
        logger.error(f"Knowledge base directory '{kb_dir}' does not exist! Please create it.")
        sys.exit(1)
        
    roles = ["ai_ml_engineer", "backend_engineer", "data_scientist"]
    
    # Check if there are any documents to ingest
    logger.info("Scanning for knowledge base documents...")
    
    for role in roles:
        filename = f"{role}.md"
        file_path = os.path.join(kb_dir, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found for role '{role}': {file_path}")
            continue
            
        logger.info(f"Processing '{filename}' for role '{role}'...")
        
        # 1. Read document text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                doc_text = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            continue
            
        # 2. Clear existing chunks for this document to avoid duplicates
        try:
            deleted_count = db.query(RAGChunk).filter(
                RAGChunk.role == role, 
                RAGChunk.document_name == filename
            ).delete()
            db.commit()
            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} existing chunks for '{filename}'.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing old chunks: {e}")
            
        # 3. Ingest document (splits into chunks, generates vectors, writes to database)
        try:
            rag_service.ingest_document(db, role, filename, doc_text)
            logger.info(f"Successfully ingested knowledge base for role: {role}")
        except Exception as e:
            logger.error(f"Failed to ingest knowledge base for role: {role}. Error: {e}")
            
    db.close()
    logger.info("Ingestion process completed.")

if __name__ == "__main__":
    main()
