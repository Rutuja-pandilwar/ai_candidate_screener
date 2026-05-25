import re

class LanguageValidator:
    def __init__(self):
        # Compiled regex to detect native Devanagari (Hindi) script characters
        self.devanagari_regex = re.compile(r"[\u0900-\u097F]+")
        
        # Compiled regex to intercept strong Romanized Hindi/Hinglish vocabulary markers
        # These are highly unique to Hindi and do not overlap with common English vocabulary.
        self.hinglish_keywords = re.compile(
            r"\b("
            r"hai|hain|tha|thi|mene|maine|mujhe|apko|aapko|tera|kaise|kab|kyun|kyu|aur|toh|bhi|liye|"
            r"rha|raha|rhi|rahi|rhey|rahe|kar|krna|karna|kuch|kuchh|kya|haan|nahi|nahin|sath|saath|yaar|yarr|bhai|"
            r"achha|thik|theek|karo|gaya|gaye|gayi|diya|liya|kiya|karta|karti|karte"
            r")\b",
            re.IGNORECASE
        )

    def validate_answer(self, text: str) -> tuple[bool, str]:
        """
        Validates if the candidate's answer is written in English only.
        Returns a tuple: (is_valid: bool, polite_error_message: str)
        """
        text = (text or "").strip()
        if not text:
            return False, "Response is completely empty. Please provide a detailed answer in English."

        # 1. Intercept Devanagari Script (Native Hindi characters)
        if self.devanagari_regex.search(text):
            return False, "It looks like you responded using Devanagari script. Please rewrite your answer strictly in English to continue."

        # 2. Intercept Hinglish (Romanized Hindi)
        # Find all matches for Hinglish keywords
        matches = self.hinglish_keywords.findall(text)
        unique_matches = set(matches)
        
        # If there are strong Hinglish matches present (2 or more distinct keywords, or 1 keyword in a short sentence)
        if len(unique_matches) >= 2 or (len(unique_matches) >= 1 and len(text.split()) < 12):
            return False, "It looks like you responded in Hindi/Hinglish. Please rewrite your answer strictly in English to continue."

        return True, "Success"
