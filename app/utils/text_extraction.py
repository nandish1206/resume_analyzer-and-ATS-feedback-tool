
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class ResumeExtractionError(Exception):
    """Raised when resume text cannot be extracted."""


def clean_extracted_text(text):
    """Normalize extracted text for downstream AI processing."""
    if not text:
        return ""

    # Remove null and other unwanted control characters.
    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize line endings and non-breaking spaces.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    # Remove trailing whitespace without destroying paragraph breaks.
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces and tabs within lines.
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def extract_pdf_text(file_path):
    """Extract text from all pages of a PDF."""
    try:
        reader = PdfReader(str(file_path))

        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    raise ResumeExtractionError(
                        "The PDF is password-protected."
                    )
            except ResumeExtractionError:
                raise
            except Exception as exc:
                raise ResumeExtractionError(
                    "The PDF is password-protected or unreadable."
                ) from exc

        page_texts = []

        for page in reader.pages:
            try:
                page_texts.append(page.extract_text() or "")
            except Exception as exc:
                raise ResumeExtractionError(
                    "Unable to extract text from a PDF page."
                ) from exc

        text = clean_extracted_text("\n\n".join(page_texts))

        if not text:
            raise ResumeExtractionError(
                "No readable text was found. The PDF may be image-only "
                "and require OCR."
            )

        return text

    except ResumeExtractionError:
        raise
    except Exception as exc:
        raise ResumeExtractionError(
            "The PDF file is invalid, corrupted, or unreadable."
        ) from exc


def extract_docx_text(file_path):
    """Extract paragraphs and table content from a DOCX document."""
    try:
        document = Document(str(file_path))
        parts = []

        # Preserve document paragraph order as far as python-docx allows.
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                parts.append(paragraph.text)

        # Many resumes place skills and experience inside tables.
        for table in document.tables:
            for row in table.rows:
                cells = [
                    clean_extracted_text(cell.text)
                    for cell in row.cells
                ]
                cells = [cell for cell in cells if cell]

                if cells:
                    parts.append(" | ".join(cells))

        text = clean_extracted_text("\n".join(parts))

        if not text:
            raise ResumeExtractionError(
                "No readable text was found in the DOCX file."
            )

        return text

    except ResumeExtractionError:
        raise
    except Exception as exc:
        raise ResumeExtractionError(
            "The DOCX file is invalid, corrupted, or unreadable."
        ) from exc


def extract_resume_text(file_path):
    """Extract clean text based on the file extension."""
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(path)

    if extension == ".docx":
        return extract_docx_text(path)

    raise ResumeExtractionError(
        "Unsupported format. Please upload a PDF or DOCX file."
    )
