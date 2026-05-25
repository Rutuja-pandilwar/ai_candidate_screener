class Chunker:
    def split(self, text: str, chunk_size: int = 400):
        """
        Split text into word-based chunks.
        Used in RAG pipeline before embedding/vector storage.
        """

        if not text:
            return []

        words = text.split()
        chunks = []

        # Create chunks of fixed word size
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size]).strip()
            if chunk:
                chunks.append(chunk)

        return chunks