from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Upload a document (PDF/image), run OCR, return extracted structured data.
    The file is DELETED immediately after extraction.
    Data is NOT saved to DB — frontend must confirm then call the correct resource API.
    """
    return await ocr_service.extract_from_upload(file, current_user, db)
