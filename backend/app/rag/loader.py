from pypdf import PdfReader
import os


class Loader:
    def load(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.split(".")[-1].lower()

        if ext == "pdf":
            reader = PdfReader(file_path)
            text = ""

            for page in reader.pages:
                text += page.extract_text() or ""

            return text

        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            raise ValueError(f"Unsupported file type: {ext}")