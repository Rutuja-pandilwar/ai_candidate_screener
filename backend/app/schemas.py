from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Candidate schemas
class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_level: Optional[str] = None
    domain_exposure: Optional[List[str]] = []

class CandidateCreate(CandidateBase):
    parsed_text: str

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Session schemas
class SessionCreate(BaseModel):
    role: str  # ai_ml_engineer, backend_engineer, data_scientist

class SessionResponse(BaseModel):
    id: str
    candidate_id: int
    selected_role: str
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    class Config:
        from_attributes = True

# Question schemas
class QuestionResponse(BaseModel):
    id: int
    session_id: str
    question_text: str
    difficulty: Optional[str] = None
    created_at: datetime
    # We omit context_retrieved and correct_answer_guideline for candidates during the test!
    class Config:
        from_attributes = True

class QuestionDetailResponse(QuestionResponse):
    context_retrieved: Optional[str] = None
    correct_answer_guideline: Optional[str] = None
    candidate_answer: Optional[str] = None
    evaluation_feedback: Optional[str] = None
    score: Optional[float] = None

# Answer submission schemas
class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str

class AnswerResponse(BaseModel):
    question_id: int
    score: float
    evaluation_feedback: str
    is_finished: bool  # True if the interview has reached max questions

# Report/Final evaluation schemas
class ReportResponse(BaseModel):
    session_id: str
    selected_role: str
    candidate_name: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    summary_report: Optional[Dict[str, Any]] = None  # Parsed JSON report
    questions: List[QuestionDetailResponse] = []
    class Config:
        from_attributes = True
