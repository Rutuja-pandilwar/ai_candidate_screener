import os
import sys
import json
import shutil
import unittest
from datetime import datetime

# Add backend app directory to python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.config import settings

# Force using a test database during verification to avoid clobbering production
TEST_DB_URL = "sqlite:///./test_candidate_screener.db"
settings.DATABASE_URL = TEST_DB_URL
settings.UPLOAD_DIR = "./test_data/uploads"
settings.KNOWLEDGE_BASE_DIR = "./test_data/knowledge"

from app.database import engine, Base, SessionLocal
from app.models import Candidate, InterviewSession, InterviewQuestion, RAGChunk
from app.services.llm_service import LLMService
from app.services.resume_parser import ResumeParser
from app.rag.rag_service import RAGService
from app.services.session_manager import SessionManager
from app.main import app as fastapi_app

class TestCandidateScreenerSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create clean directories
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.KNOWLEDGE_BASE_DIR, exist_ok=True)
        
        # Write temporary mock syllabus files
        cls.mock_ml_syllabus = """
        # Machine Learning Syllabus
        Supervised learning is where the model learns on labeled data.
        Support Vector Machines (SVM) maximize the margin between classes.
        Overfitting is when a model fits training noise and generalises poorly.
        Mitigate overfitting using regularization: L1 (Lasso) and L2 (Ridge).
        """
        with open(os.path.join(settings.KNOWLEDGE_BASE_DIR, "ai_ml_engineer.md"), "w", encoding="utf-8") as f:
            f.write(cls.mock_ml_syllabus)
            
        cls.mock_backend_syllabus = """
        # Backend Engineering Syllabus
        REST APIs use standard HTTP verbs (GET, POST, PUT, DELETE).
        ACID properties guarantee relational database transaction reliability.
        CAP Theorem states you cannot have Consistency, Availability, and Partition Tolerance simultaneously.
        """
        with open(os.path.join(settings.KNOWLEDGE_BASE_DIR, "backend_engineer.md"), "w", encoding="utf-8") as f:
            f.write(cls.mock_backend_syllabus)

        # Build database tables
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        # Clean up database file and directories
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        
        db_file = TEST_DB_URL.replace("sqlite:///", "")
        if os.path.exists(db_file):
            os.remove(db_file)
            
        if os.path.exists("test_data"):
            shutil.rmtree("test_data")
            
        if os.path.exists("./data"):
            shutil.rmtree("./data")

    def test_01_llm_service_fallback(self):
        """Verify LLM service can generate responses and fall back gracefully if no key is set."""
        llm = LLMService()
        self.assertIsNotNone(llm)
        
        # Test resume analysis
        profile = llm.analyze_resume("Jane Doe. email: jane@test.com. Skills: Python, SQL.")
        self.assertIn("name", profile)
        self.assertIn("email", profile)
        self.assertIn("skills", profile)
        
        # Test question generator
        question = llm.generate_interview_question(
            role="backend_engineer",
            candidate_profile={"skills": ["Python"], "experience_level": "mid"},
            rag_context="REST APIs use GET and POST verbs.",
            previous_questions_text=[]
        )
        self.assertIn("question_text", question)
        self.assertIn("correct_answer_guideline", question)
        self.assertIn("difficulty", question)

    def test_02_rag_chunking_and_ingestion(self):
        """Verify document splitting and database vector indexation."""
        llm = LLMService()
        rag = RAGService(llm)
        
        # Verify custom chunking logic
        chunks = rag.chunk_text(self.mock_ml_syllabus, chunk_size=100, overlap=10)
        self.assertTrue(len(chunks) > 0)
        
        # Ingest mock document
        rag.ingest_document(self.db, "ai_ml_engineer", "ai_ml_engineer.md", self.mock_ml_syllabus)
        
        # Count chunks in SQLite
        db_chunks = self.db.query(RAGChunk).filter(RAGChunk.role == "ai_ml_engineer").all()
        self.assertTrue(len(db_chunks) > 0)
        
        # Retrieve chunks using vector similarity
        retrieved = rag.retrieve(self.db, "ai_ml_engineer", "Tell me about overfitting and regularization", top_k=2)
        self.assertTrue(len(retrieved) > 0)
        self.assertIn("text", retrieved[0])
        self.assertTrue(retrieved[0]["score"] > 0.0)

    def test_03_session_orchestration_flow(self):
        """Verify the complete interview state lifecycle: start, ask, grade, and finalize report."""
        llm = LLMService()
        # Ingest backend knowledge base so retrieval succeeds
        rag = RAGService(llm)
        rag.ingest_document(self.db, "backend_engineer", "backend_engineer.md", self.mock_backend_syllabus)
        
        parser = ResumeParser(llm)
        manager = SessionManager(llm, parser, rag)
        
        # Create a mock resume file
        resume_path = os.path.join(settings.UPLOAD_DIR, "resume.txt")
        with open(resume_path, "w", encoding="utf-8") as f:
            f.write("Alice Smith\nalice@example.com\nExperience: 4 years\nSkills: FastAPI, SQL, Docker")
            
        # 1. Create Session
        session = manager.create_session(self.db, resume_path, "backend_engineer")
        self.assertIsNotNone(session)
        self.assertEqual(session.status, "started")
        self.assertEqual(session.selected_role, "backend_engineer")
        
        # 2. Get Next Question
        question = manager.get_next_question(self.db, session.id)
        self.assertIsNotNone(question)
        self.assertIsNotNone(question.question_text)
        self.assertIsNotNone(question.correct_answer_guideline)
        self.assertIsNotNone(question.context_retrieved)
        
        # 3. Submit Candidate Answer and Evaluate
        result = manager.submit_answer(
            db=self.db,
            session_id=session.id,
            question_id=question.id,
            answer_text="REST APIs use GET for idempotent reading and POST for creating resources. They are standard HTTP protocols."
        )
        
        self.assertEqual(result["question_id"], question.id)
        self.assertTrue(result["score"] >= 1.0 and result["score"] <= 10.0)
        self.assertIsNotNone(result["evaluation_feedback"])
        
        # 4. Finalize early to verify report generator compiles
        final_session = manager.finalize_interview(self.db, session.id)
        self.assertEqual(final_session.status, "completed")
        self.assertIsNotNone(final_session.overall_score)
        self.assertIsNotNone(final_session.summary_report)
        
        # Verify JSON report structure
        report = json.loads(final_session.summary_report)
        self.assertIn("overall_score", report)
        self.assertIn("strengths", report)
        self.assertIn("areas_for_improvement", report)
        self.assertIn("summary", report)

    def test_04_fastapi_app_initialization(self):
        """Verify the FastAPI routing compilation on startup."""
        self.assertIsNotNone(fastapi_app)
        self.assertEqual(fastapi_app.title, "AI-Powered Role-Based Candidate Screening System")

if __name__ == "__main__":
    unittest.main()
