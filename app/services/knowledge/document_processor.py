
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


class DocumentProcessor:
    """Extract text from supported knowledge-base documents."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

    def extract_text(
        self,
        file_content: bytes,
        filename: str,
    ) -> str:
        if not file_content:
            raise ValueError("Uploaded document is empty.")

        extension = Path(filename).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                "Only PDF and TXT files are supported."
            )

        if extension == ".pdf":
            extracted_text = self._extract_pdf(file_content)
        else:
            extracted_text = self._extract_txt(file_content)

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise ValueError(
                "No readable text was found in the document."
            )

        return extracted_text

    @staticmethod
    def _extract_pdf(file_content: bytes) -> str:
        reader = PdfReader(BytesIO(file_content))

        pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        return "\n\n".join(pages)

    @staticmethod
    def _extract_txt(file_content: bytes) -> str:
        try:
            return file_content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(
                "TXT file must use UTF-8 encoding."
            ) from error


document_processor = DocumentProcessor()
