import os
import json
import logging
import uuid

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# =========================
# PROJECT IMPORTS
# =========================
from app.config import settings
from app.database import init_db, get_db
from app.models import InterviewSession, InterviewQuestion, Candidate

from app.schemas import (
    SessionResponse,
    QuestionResponse,
    AnswerSubmit,
    AnswerResponse,
    ReportResponse,
    QuestionDetailResponse
)

from app.services.llm_service import LLMService
from app.services.resume_parser import ResumeParser
from app.rag.rag_service import RAGService   # ✅ FIXED IMPORT
from app.services.session_manager import SessionManager


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =========================
# FASTAPI APP
# =========================
app = FastAPI(
    title="AI-Powered Role-Based Candidate Screening System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# SERVICES (SINGLETONS)
# =========================
llm_service = LLMService()
resume_parser = ResumeParser(llm_service)

# ✅ FIX: no llm_service passed
rag_service = RAGService()

session_manager = SessionManager(llm_service, resume_parser, rag_service)


# =========================
# STARTUP EVENT
# =========================
@app.on_event("startup")
async def startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

    # =========================
    # RAG INITIALIZATION
    # =========================
    try:
        kb_path = settings.KNOWLEDGE_BASE_DIR
        if os.path.exists(kb_path):
            rag_service.build_index(kb_path)
            logger.info("RAG knowledge base loaded successfully")
        else:
            logger.warning(f"Knowledge base not found: {kb_path}")

    except Exception as e:
        logger.error(f"RAG initialization failed: {e}")

    logger.info("Startup complete")


# =========================
# HEALTH CHECK
# =========================
@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini": llm_service.enabled,
        "gemini_api_configured": llm_service.enabled
    }


# =========================
# START SESSION
# =========================
@app.post("/api/sessions/start", response_model=SessionResponse)
async def start_session(
    role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if role not in ["ai_ml_engineer", "backend_engineer", "data_scientist"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    temp_path = os.path.join(
        settings.UPLOAD_DIR,
        f"{uuid.uuid4()}_{file.filename}"
    )

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        session = session_manager.create_session(db, temp_path, role)
        return session

    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# =========================
# NEXT QUESTION (RAG FLOW)
# =========================
@app.post("/api/sessions/{session_id}/next-question", response_model=QuestionResponse)
def next_question(session_id: str, db: Session = Depends(get_db)):

    try:
        question = session_manager.get_next_question(db, session_id)

        if not question:
            raise HTTPException(status_code=400, detail="Session completed")

        return question

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# SUBMIT ANSWER
# =========================
@app.post("/api/sessions/{session_id}/submit-answer", response_model=AnswerResponse)
def submit_answer(session_id: str, payload: AnswerSubmit, db: Session = Depends(get_db)):

    try:
        return session_manager.submit_answer(
            db,
            session_id,
            payload.question_id,
            payload.answer_text
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# REPORT
# =========================
@app.get("/api/sessions/{session_id}/report", response_model=ReportResponse)
def report(session_id: str, db: Session = Depends(get_db)):

    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    candidate = db.query(Candidate).filter(
        Candidate.id == session.candidate_id
    ).first()

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).all()

    try:
        report_data = json.loads(session.summary_report) if session.summary_report else {}
    except:
        report_data = {}

    return ReportResponse(
        session_id=session.id,
        selected_role=session.selected_role,
        candidate_name=candidate.name if candidate else "Candidate",
        created_at=session.created_at,
        finished_at=session.finished_at,
        overall_score=session.overall_score,
        summary_report=report_data,
        questions=[
            QuestionDetailResponse(
                id=q.id,
                session_id=q.session_id,
                question_text=q.question_text,
                difficulty=q.difficulty,
                created_at=q.created_at,
                context_retrieved=q.context_retrieved,
                correct_answer_guideline=q.correct_answer_guideline,
                candidate_answer=q.candidate_answer,
                evaluation_feedback=q.evaluation_feedback,
                score=q.score
            )
            for q in questions
        ]
    )


# =========================
# END SESSION
# =========================
@app.post("/api/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: str, db: Session = Depends(get_db)):

    try:
        return session_manager.finalize_interview(db, session_id)

    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))