"""
OCR Service
───────────
Workflow:
  1. Accept uploaded file (PDF or image)
  2. Convert PDF pages to images if needed
  3. Run Tesseract OCR on each image
  4. Parse structured fields via heuristic regex + keyword matching
  5. Return extracted JSON to frontend for confirmation
  6. Delete the uploaded file immediately after extraction

No data is saved to DB here — the frontend confirms then calls the
respective resource API (obligations, receivables, etc.)
"""

import os
import re
import uuid
import logging
import tempfile
from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.utils.audit import write_audit_log
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Configure Tesseract executable path
if settings.TESSERACT_CMD and settings.TESSERACT_CMD != "tesseract":
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
MAX_FILE_SIZE_MB = 10


async def extract_from_upload(
    file: UploadFile,
    user_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Main OCR entry point. Returns structured data extracted from the document.
    The temp file is deleted before returning.
    """
    _validate_file(file)

    suffix = Path(file.filename).suffix.lower()
    tmp_path: Path | None = None

    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                )
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # Extract text
        raw_text = _extract_text(tmp_path, suffix)

        # Parse structured fields
        extracted = _parse_financial_data(raw_text)
        extracted["raw_text_preview"] = raw_text[:500]  # for frontend debugging

        await write_audit_log(
            db,
            action="OCR_UPLOAD",
            user_id=user_id,
            resource="document",
            extra={"filename": file.filename, "doc_type": extracted.get("document_type")},
        )
        return extracted

    finally:
        # SECURITY: always delete the file
        if tmp_path and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except Exception:
                logger.warning("Could not delete temp file: %s", tmp_path)


def _validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )


def _extract_text(path: Path, suffix: str) -> str:
    """Convert file to text via Tesseract. Handles both images and PDFs."""
    try:
        if suffix == ".pdf":
            return _extract_from_pdf(path)
        else:
            img = Image.open(path)
            return pytesseract.image_to_string(img, lang="eng")
    except Exception as exc:
        logger.error("OCR extraction failed: %s", exc)
        raise HTTPException(status_code=500, detail="OCR processing failed") from exc


def _extract_from_pdf(path: Path) -> str:
    """Convert PDF pages to images then extract text."""
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(str(path), dpi=200)
        texts = [pytesseract.image_to_string(page, lang="eng") for page in pages]
        return "\n".join(texts)
    except ImportError:
        raise HTTPException(status_code=500, detail="pdf2image not installed for PDF support")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {exc}") from exc


def _parse_financial_data(text: str) -> dict[str, Any]:
    """
    Heuristic extraction of financial fields from raw OCR text.
    Returns a best-effort structured dict for frontend confirmation.
    """
    text_lower = text.lower()
    result: dict[str, Any] = {
        "document_type": _detect_doc_type(text_lower),
        "vendor_name": _extract_pattern(text, r"(?:from|vendor|supplier|payee)[:\s]+([A-Za-z0-9\s&.,'-]+)", 1),
        "client_name": _extract_pattern(text, r"(?:to|bill to|client|customer)[:\s]+([A-Za-z0-9\s&.,'-]+)", 1),
        "amount": _extract_amount(text),
        "invoice_number": _extract_pattern(text, r"(?:invoice\s*#?|inv\s*no\.?)[:\s]*([A-Za-z0-9/-]+)", 1),
        "date": _extract_pattern(text, r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", 0),
        "due_date": _extract_pattern(text, r"(?:due\s*date|payment\s*due)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", 1),
        "gst_number": _extract_pattern(text, r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1})\b", 0),
        "line_items": [],
    }

    # Extract line items (amount per row)
    for match in re.finditer(r"([A-Za-z\s]+)\s+(\d+)\s+[\₹$]?\s*([\d,]+\.?\d*)", text):
        result["line_items"].append({
            "description": match.group(1).strip(),
            "quantity": match.group(2),
            "amount": match.group(3).replace(",", ""),
        })

    return result


def _detect_doc_type(text_lower: str) -> str:
    if "invoice" in text_lower:
        return "invoice"
    if "receipt" in text_lower:
        return "receipt"
    if "expense" in text_lower or "reimbursement" in text_lower:
        return "expense"
    if "loan" in text_lower or "credit" in text_lower or "disbursal" in text_lower:
        return "loan"
    return "unknown"


def _extract_pattern(text: str, pattern: str, group: int) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            return m.group(group).strip()
        except IndexError:
            pass
    return None


def _extract_amount(text: str) -> float | None:
    # Match numbers like ₹1,23,456.78 or $1234.56 or just 12345
    amounts = re.findall(r"(?:₹|\$|INR|Rs\.?)\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
    if amounts:
        try:
            return float(amounts[-1].replace(",", ""))
        except ValueError:
            pass
    # Fallback: largest standalone number
    nums = re.findall(r"\b(\d{3,}(?:,\d{3})*(?:\.\d{1,2})?)\b", text)
    if nums:
        try:
            return max(float(n.replace(",", "")) for n in nums)
        except ValueError:
            pass
    return None
