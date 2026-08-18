import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import PDFUpload, Student
from app.schemas import PDFUploadOut
from app.security import get_current_student, require_admin
from app.services.pdf_service import extract_text

router = APIRouter(prefix="/uploads", tags=["PDF Uploads"])

MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


@router.post("", response_model=PDFUploadOut, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    subject: str = Form(...),
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.MAX_UPLOAD_MB}MB limit.")

    student_dir = settings.UPLOAD_DIR / str(current.student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest_path = student_dir / safe_name
    dest_path.write_bytes(contents)

    record = PDFUpload(
        student_id=current.student_id,
        filename=file.filename,
        filepath=str(dest_path),
        subject=subject,
        size_bytes=len(contents),
        status="processing",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        text, page_count = extract_text(dest_path)
        record.extracted_text = text
        record.page_count = page_count
        record.status = "ready" if text.strip() else "failed"
    except Exception:
        record.status = "failed"
    db.commit()
    db.refresh(record)

    return record


@router.get("", response_model=list[PDFUploadOut])
def list_my_uploads(db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    return (
        db.query(PDFUpload)
        .filter(PDFUpload.student_id == current.student_id)
        .order_by(PDFUpload.upload_date.desc())
        .all()
    )


@router.get("/{pdf_id}", response_model=PDFUploadOut)
def get_upload(pdf_id: int, db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    record = db.query(PDFUpload).filter(PDFUpload.pdf_id == pdf_id, PDFUpload.student_id == current.student_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found.")
    return record


@router.delete("/{pdf_id}", status_code=204)
def delete_upload(pdf_id: int, db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    record = db.query(PDFUpload).filter(PDFUpload.pdf_id == pdf_id, PDFUpload.student_id == current.student_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found.")
    Path(record.filepath).unlink(missing_ok=True)
    db.delete(record)
    db.commit()
    return None
