import os
import pypdf
import logging
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or TXT files."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found at {file_path}")

        _, file_extension = os.path.splitext(file_path.lower())
        
        if file_extension == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif file_extension in [".txt", ".md"]:
            return self._extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Use PDF or TXT.")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF using pypdf."""
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                num_pages = len(reader.pages)
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {e}")
            raise RuntimeError(f"Could not parse PDF resume: {e}")

    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text content from a TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise RuntimeError(f"Could not read text resume: {e}")

    def parse_resume(self, file_path: str) -> dict:
        """Parse file and return a structured candidate profile dictionary."""
        logger.info(f"Starting parsing for resume: {file_path}")
        raw_text = self.extract_text_from_file(file_path)
        
        if not raw_text:
            raise ValueError("Resume file appears to be empty.")

        # Use the LLM service to analyze the raw text and return structured info
        profile = self.llm_service.analyze_resume(raw_text)
        return {
            "profile": profile,
            "raw_text": raw_text
        }
