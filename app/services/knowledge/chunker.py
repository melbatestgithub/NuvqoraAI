
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


class DocumentChunker:
    """Split documents into overlapping text chunks."""

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def split_text(self, text: str) -> list[str]:
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text.")

        chunks = self.splitter.split_text(text)

        return [
            chunk.strip()
            for chunk in chunks
            if chunk.strip()
        ]


document_chunker = DocumentChunker()
