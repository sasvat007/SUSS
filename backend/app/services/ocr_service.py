"""
OCR Service — Advanced Invoice Parser
──────────────────────────────────────
Workflow:
  1. Accept uploaded file (PDF or image)
  2. Try pdfplumber for text-based PDFs (fast, lossless)
  3. Fall back to Tesseract OCR with image pre-processing for scanned PDFs
  4. Parse structured fields using heuristic regex + keyword matching
     tuned for Indian GST invoice layouts
  5. Return extracted JSON to frontend for user confirmation
  6. Delete the uploaded file immediately after extraction

No data is saved to DB here — the frontend confirms and then calls
the respective resource API (obligations, receivables, etc.)
"""

import os
import re
import uuid
import logging
import tempfile
from pathlib import Path
from typing import Any
from datetime import datetime
from dateutil import parser

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.utils.audit import write_audit_log
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Configure Tesseract executable path
if settings.TESSERACT_CMD and settings.TESSERACT_CMD != "tesseract":
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Optional dependencies
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
MAX_FILE_SIZE_MB = 10


# ── Entry Point ───────────────────────────────────────────────────────────────

async def extract_from_upload(
    file: UploadFile,
    user: User,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Main OCR entry point. Predicts if it's a Receivable or Payable based on business matching.
    """
    _validate_file(file)

    suffix = Path(file.filename).suffix.lower()
    tmp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
                )
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # 2. Extract and Parse
        raw_text = _extract_text(tmp_path, suffix)
        extracted = _parse_invoice(raw_text)
        
        # 3. Smart Detection: User as Vendor = Receivable; User as Client = Payable
        biz_name = (user.business_name or "").lower()
        v_name = (extracted.get("vendor_name") or "").lower()
        c_name = (extracted.get("client_name") or "").lower()

        if biz_name and (biz_name in v_name or (len(biz_name) > 5 and biz_name[:5] in v_name)):
            extracted["suggested_type"] = "receivable"
        elif biz_name and (biz_name in c_name or (len(biz_name) > 5 and biz_name[:5] in c_name)):
            extracted["suggested_type"] = "obligation"
        else:
            # Most users upload invoices they SENT for SUSS
            extracted["suggested_type"] = "receivable" 

        extracted["raw_text_preview"] = raw_text[:500]

        await write_audit_log(
            db,
            action="OCR_UPLOAD",
            user_id=user.id,
            resource="document",
            extra={"filename": file.filename, "biz_match": extracted["suggested_type"]},
        )
        return extracted

    finally:
        if tmp_path and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except Exception:
                logger.warning("Could not delete temp file: %s", tmp_path)


# ── Validation ────────────────────────────────────────────────────────────────

def _validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


# ── Text Extraction ───────────────────────────────────────────────────────────

def _extract_text(path: Path, suffix: str) -> str:
    """Route to the best text extraction strategy based on file type."""
    try:
        if suffix == ".pdf":
            return _extract_from_pdf(str(path))
        else:
            img = Image.open(path)
            return pytesseract.image_to_string(_preprocess_image(img), config="--psm 4 --oem 3")
    except Exception as exc:
        logger.error("OCR extraction failed: %s", exc)
        raise HTTPException(status_code=500, detail="OCR processing failed") from exc


def _extract_from_pdf(pdf_path: str) -> str:
    """
    Choose strategy:
    1. pdfplumber — direct text extraction for non-scanned PDFs (fast, lossless).
    2. Tesseract OCR — render pages as images for scanned PDFs.
    """
    raw = ""

    if PDFPLUMBER_AVAILABLE:
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            raw = "\n".join(text_parts)
        except Exception as exc:
            logger.warning("pdfplumber failed, falling back to OCR: %s", exc)

    # Heuristic: if fewer than 100 chars extracted, assume it's a scanned PDF
    if len(raw.strip()) < 100:
        raw = _pdf_to_text_via_ocr(pdf_path)

    return raw


def _pdf_to_text_via_ocr(pdf_path: str, dpi: int = 300) -> str:
    """Render each PDF page to PIL image, pre-process, then run Tesseract."""
    if PDF2IMAGE_AVAILABLE:
        pages = convert_from_path(pdf_path, dpi=dpi)
    else:
        import subprocess
        import glob
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, "pg")
            subprocess.run(
                ["pdftoppm", "-jpeg", "-r", str(dpi), pdf_path, prefix],
                check=True, capture_output=True
            )
            pages = [Image.open(f) for f in sorted(glob.glob(f"{prefix}*.jpg"))]

    all_text = []
    for page_img in pages:
        processed = _preprocess_image(page_img)
        text = pytesseract.image_to_string(processed, config="--psm 4 --oem 3")
        all_text.append(text)

    return "\n".join(all_text)


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Greyscale → contrast boost → sharpen. Improves Tesseract on printed invoices."""
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


# ── Main Invoice Parser ───────────────────────────────────────────────────────

def _parse_invoice(text: str) -> dict[str, Any]:
    """Full pipeline: raw OCR text → structured JSON dict."""
    taxable, cgst, sgst, igst, total = _extract_amounts(text)

    return {
        "document_type": "invoice",
        "vendor_name": _extract_vendor_name(text),
        "client_name": _extract_client_name(text),
        "amount": round(total, 2) if total is not None else None,
        "invoice_number": _extract_invoice_number(text),
        "date": _extract_date(text),
        "due_date": None,
        "gst_number": _extract_gst_number(text),
        "tax_breakdown": {
            "taxable_value": taxable,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "total_tax": round(cgst + sgst + igst, 2),
        },
        "line_items": _extract_line_items(text),
    }


# ── Field Extractors ──────────────────────────────────────────────────────────

def _find(pattern: str, text: str, flags=re.IGNORECASE, group: int = 1) -> str | None:
    """Return the first regex match group, or None."""
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else None


def _extract_vendor_name(text: str) -> str:
    """
    The vendor (seller) is the company that issued the invoice.
    OCR often places the company name on the same line as 'Invoice No.'
    Example: 'Kuber Deco World Invoice No. Dated'
    """
    # Strategy 1: text BEFORE "Invoice No." on the same line
    m = re.search(r"^(.+?)\s+Invoice\s+No\.?\s*", text, re.IGNORECASE | re.MULTILINE)
    if m:
        candidate = m.group(1).strip()
        if candidate.upper() not in ("TAX INVOICE", "E-INVOICE", "ORIGINAL FOR RECIPIENT"):
            return candidate

    # Strategy 2: first Title-Case line with a known company-suffix keyword
    for line in text.splitlines():
        stripped = line.strip()
        if re.search(
            r"\b(Pvt\.?\s*Ltd\.?|World|Traders?|Enterprises?|Industries|Corporation|Co\.)\b",
            stripped, re.IGNORECASE
        ) and len(stripped) > 5:
            return stripped

    # Strategy 3: first non-header ALL-CAPS line
    for line in text.splitlines():
        stripped = line.strip()
        if (stripped.isupper() and len(stripped) > 5
                and stripped not in ("TAX INVOICE", "E-INVOICE", "ORIGINAL FOR RECIPIENT")):
            return stripped

    return ""


def _extract_client_name(text: str) -> str:
    """
    Consignee (Ship to) → client name.
    Strips layout noise like 'Dispatched through', 'Destination', etc.
    """
    NOISE = re.compile(
        r"\s+(Dispatched?\s+through|Destination|Terms\s+of\s+Delivery"
        r"|Mode[/\s]Terms|Delivery\s+Note|GSTIN|State\s+Name|Place\s+of).*",
        re.IGNORECASE | re.DOTALL
    )

    m = re.search(r"Consignee\s*\(Ship\s*to\)[^\n]*\n\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        name = NOISE.sub("", m.group(1)).strip()
        if name:
            return name

    m = re.search(r"Buyer\s*\(Bill\s*to\)[^\n]*\n\s*([^\n]+)", text, re.IGNORECASE)
    if m:
        return NOISE.sub("", m.group(1)).strip()

    return ""


def _extract_invoice_number(text: str) -> str | None:
    """Handles KD/SL/2227/25-26, INV/001/2026, TAX/00123 styles."""
    # Pattern A: number on NEXT line after "Invoice No."
    m = re.search(
        r"Invoice\s*No\.?\s*\n\s*([A-Z]{2,}[/\-][A-Z0-9/\-]+)",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern B: two-column layout — number on same line as label
    m = re.search(r"[A-Z]{2,}/[A-Z]{2,}/\d+/\d{2,4}-?\d{2,4}", text)
    if m:
        return m.group(0).strip()

    # Pattern C: generic INV- prefix
    return _find(r"(?:Invoice\s*No|INV)[.:\s-]*([A-Z0-9/\-]{5,})", text)


def _extract_date(text: str) -> str:
    """Handles '2-Mar-26', '02/03/2026', '02-03-2026' formats. Normalizes to YYYY-MM-DD."""
    def _parse(s):
        try:
            return parser.parse(s, dayfirst=True).date().isoformat()
        except Exception:
            return s

    inv_line_m = re.search(
        r"[A-Z]{2,}/[A-Z]{2,}/\d+/[\d\-]+.*?(\d{1,2}[-/\s][A-Za-z]+[-/\s]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        text
    )
    if inv_line_m:
        return _parse(inv_line_m.group(1).strip())

    m = re.search(
        r"Dated\s*[:\-]?\s*(\d{1,2}[-/\s][A-Za-z]+[-/\s]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        text, re.IGNORECASE
    )
    if m:
        return _parse(m.group(1).strip())

    m = re.search(r"Ack\s*Date\s*[:\-]?\s*(\S+)", text, re.IGNORECASE)
    if m:
        return _parse(m.group(1).strip())

    return ""


def _extract_gst_number(text: str) -> str:
    """Indian GST format: 2-digit state + 10-char PAN + 1Z + 1 check digit."""
    all_gst = re.findall(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9])\b", text)
    return all_gst[0] if all_gst else ""


def _extract_line_items(text: str) -> list:
    """Extract tabular line items + CGST/SGST/IGST tax sub-lines."""
    items = []

    pattern = re.compile(
        r"^\s*\d+\s*[|/]?\s*"
        r"(\d{4,6}\s+.+?)\s+"
        r"\d{6,8}\s+"
        r"[\d,\.]+\s+\w+\s+"
        r"([\d,]+\.\d{2})\s+\w+",
        re.MULTILINE
    )
    for m in pattern.finditer(text):
        desc = re.sub(r"\s+", " ", m.group(1)).strip(" |/")
        if desc:
            items.append({"description": desc, "amount": m.group(2).replace(",", "")})

    for tax_label in ("CGST", "SGST", "IGST", "CESS", "UTGST"):
        m = re.search(
            rf"{tax_label}\s*(?:A/c|@\s*[\d.]+%)?\s+([\d,]+\.\d{{2}})",
            text, re.IGNORECASE
        )
        if m:
            items.append({"description": f"{tax_label} Tax", "amount": m.group(1).replace(",", "")})

    return items


def _extract_amounts(text: str) -> tuple:
    """Returns (taxable_value, cgst, sgst, igst, total_amount)."""
    total = None
    for pattern in [
        r"Total\s*[\d,]*\s*NOS\s*[=₹\u20b9]?\s*([\d,]+\.\d{2})",
        r"(?:Grand\s*Total|Invoice\s*Total|Total\s*Amount)\s*[:\-=₹\u20b9]?\s*([\d,]+\.\d{2})",
        r"[=₹\u20b9]\s*([\d,]+\.\d{2})\s*$",
    ]:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            total = float(m.group(1).replace(",", ""))
            break

    taxable_str = _find(r"Taxable\s*Value\s*[\n\r]+\s*([\d,]+\.\d{2})", text)
    if not taxable_str:
        taxable_str = _find(r"\d{8}\s+([\d,]+\.\d{2})\s+\d+%", text)
    taxable_val = float(taxable_str.replace(",", "")) if taxable_str else None

    cgst_m = re.search(r"CGST\s*(?:A/c)?\s+([\d,]+\.\d{2})", text, re.IGNORECASE)
    cgst = float(cgst_m.group(1).replace(",", "")) if cgst_m else 0.0

    sgst_m = re.search(r"(?:SGST|UTGST)\s*(?:A/c)?\s+([\d,]+\.\d{2})", text, re.IGNORECASE)
    sgst = float(sgst_m.group(1).replace(",", "")) if sgst_m else 0.0

    igst_m = re.search(r"IGST\s*(?:A/c)?\s+([\d,]+\.\d{2})", text, re.IGNORECASE)
    igst = float(igst_m.group(1).replace(",", "")) if igst_m else 0.0

    if total is None and taxable_val is not None:
        total = taxable_val + cgst + sgst + igst

    return taxable_val, cgst, sgst, igst, total


# ── Legacy compatibility (kept for existing callers) ──────────────────────────

def _parse_financial_data(text: str) -> dict[str, Any]:
    """Alias kept for backward compatibility."""
    return _parse_invoice(text)
