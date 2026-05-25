import uuid
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Candidate, InterviewSession, InterviewQuestion
from app.services.llm_service import LLMService
from app.services.resume_parser import ResumeParser
from app.rag.rag_service import RAGService

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, llm_service: LLMService, resume_parser: ResumeParser, rag_service: RAGService):
        self.llm_service = llm_service
        self.resume_parser = resume_parser
        self.rag_service = rag_service

    def create_session(self, db: Session, resume_file_path: str, role: str) -> InterviewSession:
        """Parse resume, save candidate info, and start an interview session."""
        logger.info(f"Creating interview session for role '{role}' with resume '{resume_file_path}'")
        
        # 1. Parse the resume
        parsed_data = self.resume_parser.parse_resume(resume_file_path)
        profile = parsed_data["profile"]
        raw_text = parsed_data["raw_text"]

        # 2. Store Candidate in DB
        candidate = Candidate(
            name=profile.get("name", "Unknown Candidate"),
            email=profile.get("email", "unknown@example.com"),
            skills=json.dumps(profile.get("skills", [])),
            experience_level=profile.get("experience_level", "mid"),
            domain_exposure=json.dumps(profile.get("domain_exposure", [])),
            parsed_text=raw_text
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        # 3. Create Session
        session_id = str(uuid.uuid4())
        session = InterviewSession(
            id=session_id,
            candidate_id=candidate.id,
            selected_role=role,
            status="started",
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Created session {session_id} successfully for candidate {candidate.name}")
        return session

    def get_next_question(self, db: Session, session_id: str) -> InterviewQuestion:
        """Generate the next interview question for the session."""
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        if session.status == "completed":
            return None

        # Check existing questions
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()

        # Check if max questions reached
        if len(questions) >= settings.MAX_QUESTIONS:
            logger.info("Maximum questions reached. Completing session.")
            self.finalize_interview(db, session_id)
            return None

        # Load candidate profile
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        skills = json.loads(candidate.skills)
        domain = json.loads(candidate.domain_exposure)
        candidate_profile = {
            "skills": skills,
            "experience_level": candidate.experience_level,
            "domain_exposure": domain
        }

        # 4. Construct RAG Search Query dynamically
        # We vary the query based on the question index to cover different topics
        question_idx = len(questions)
        search_topics = {
            "ai_ml_engineer": [
                "Decision Trees overfitting, entropy, pruning, concepts",
                "Support Vector Machines, Linear Logistic regression, bias-variance tradeoff",
                "Maximum likelihood estimation, MAP, Bayes Theorem, probability",
                "Neural networks, feedforward, backpropagation, regularization",
                "Generative AI, Retrieval Augmented Generation RAG, LLMs"
            ],
            "backend_engineer": [
                "REST APIs, GraphQL, gRPC, status codes, API protocols",
                "Relational Databases, Normalization 1NF 2NF 3NF, Denormalization, ACID properties",
                "CAP Theorem, Consistency Availability Partition, NoSQL MongoDB Redis Cassandra",
                "Caching strategies, cache-aside write-through, cache eviction LRU LFU",
                "Message Queues, RabbitMQ, Kafka, Concurrency vs Parallelism, JWT Auth security"
            ],
            "data_scientist": [
                "Exploratory Data Analysis EDA, Outliers IQR, Statistics Hypothesis Testing p-value",
                "Feature Selection filter wrapper, Data Preprocessing Standardization normalization",
                "Supervised algorithms Decision Trees Gini, Ensemble Methods Random Forest Bagging",
                "Boosting algorithms AdaBoost Gradient Boosting XGBoost LightGBM",
                "Model Evaluation Confusion Matrix Precision Recall F1 ROC-AUC, cross-validation"
            ]
        }

        # Fallback query content
        role_topics = search_topics.get(session.selected_role, search_topics["backend_engineer"])
        topic_query = role_topics[question_idx % len(role_topics)]
        
        # Merge candidate skill context to retrieve custom relevant sections if possible
        # e.g., if candidate knows PyTorch, query for neural network topics.
        rel_skills = [s for s in skills if s.lower() in topic_query.lower()]
        query = f"{topic_query} - Candidate skills: {', '.join(rel_skills) if rel_skills else 'general'}"

        # 5. Retrieve Context via RAG
        retrieved_chunks = self.rag_service.retrieve(db, session.selected_role, query, top_k=2)
        
        # Build context string
        context_str = "\n\n".join([f"[Source: {c['document_name']}] {c['text']}" for c in retrieved_chunks])
        if not context_str:
            context_str = "No grounded context available."

        # Keep trace of retrieved chunks metadata
        context_metadata = json.dumps([
            {"document": c["document_name"], "chunk_id": c["chunk_id"], "score": c["score"]} 
            for c in retrieved_chunks
        ])

        # Get previous questions' text to prevent redundancy
        prev_questions = [q.question_text for q in questions]

        # 6. Generate Question via LLM
        question_data = self.llm_service.generate_interview_question(
            role=session.selected_role,
            candidate_profile=candidate_profile,
            rag_context=context_str,
            previous_questions_text=prev_questions
        )

        # 7. Save Question
        new_question = InterviewQuestion(
            session_id=session_id,
            question_text=question_data["question_text"],
            context_retrieved=context_metadata,
            correct_answer_guideline=question_data["correct_answer_guideline"],
            difficulty=question_data["difficulty"],
            created_at=datetime.utcnow()
        )
        db.add(new_question)
        
        # Update session status if first question
        if session.status == "started":
            session.status = "in_progress"
            
        db.commit()
        db.refresh(new_question)
        
        logger.info(f"Generated next question {new_question.id} for session {session_id}")
        return new_question

    def submit_answer(self, db: Session, session_id: str, question_id: int, answer_text: str) -> dict:
        """Evaluate candidate's response to the active question."""
        logger.info(f"Submitting answer for question {question_id} in session {session_id}")
        
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id, 
            InterviewQuestion.session_id == session_id
        ).first()
        
        if not question:
            raise ValueError(f"Question {question_id} not found for this session.")

        # 1. Validate Language (English Only)
        from app.services.validator import LanguageValidator
        validator = LanguageValidator()
        is_valid, err_msg = validator.validate_answer(answer_text)
        if not is_valid:
            raise ValueError(err_msg)

        # 8. Evaluate Answer via LLM
        evaluation = self.llm_service.evaluate_candidate_answer(
            question_text=question.question_text,
            correct_guideline=question.correct_answer_guideline,
            candidate_answer=answer_text
        )

        # Save candidate response and evaluation
        question.candidate_answer = answer_text
        question.evaluation_feedback = evaluation["evaluation_feedback"]
        question.score = float(evaluation["score"])
        db.commit()

        # Check if interview is finished
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()
        answered_count = len([q for q in questions if q.candidate_answer is not None])
        
        is_finished = answered_count >= settings.MAX_QUESTIONS
        if is_finished:
            self.finalize_interview(db, session_id)
            db.refresh(session)

        return {
            "question_id": question_id,
            "score": question.score,
            "evaluation_feedback": question.evaluation_feedback,
            "is_finished": is_finished
        }

    def finalize_interview(self, db: Session, session_id: str) -> InterviewSession:
        """Calculate final score, build insights dashboard report, and end session."""
        logger.info(f"Finalizing session: {session_id}")
        
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session or session.status == "completed":
            return session

        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()

        # Collect Q&As for final report processing
        qa_pairs = []
        scores = []
        for q in questions:
            if q.score is not None:
                scores.append(q.score)
                qa_pairs.append({
                    "question": q.question_text,
                    "answer": q.candidate_answer or "[No Answer]",
                    "score": q.score,
                    "feedback": q.evaluation_feedback or ""
                })

        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Generate final dashboard report via LLM
        report_data = self.llm_service.generate_final_report(
            candidate_name=candidate.name,
            role=session.selected_role,
            qa_pairs=qa_pairs
        )

        # Update Session
        session.status = "completed"
        session.finished_at = datetime.utcnow()
        session.overall_score = float(report_data.get("overall_score", overall_score))
        session.summary_report = json.dumps(report_data)
        
        db.commit()
        db.refresh(session)
        
        logger.info(f"Session {session_id} successfully closed with score {session.overall_score}")
        return session
