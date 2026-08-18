from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, PDFUpload, Quiz, Flashcard, StreakRecord
from app.schemas import AdminDashboardOut, StudentOut, PDFUploadOut
from app.security import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def dashboard(db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    total_students = db.query(Student).count()
    total_pdfs = db.query(PDFUpload).count()
    total_quizzes = db.query(Quiz).count()
    total_flashcards = db.query(Flashcard).count()

    top = (
        db.query(StreakRecord)
        .order_by(StreakRecord.quizzes_completed.desc())
        .limit(5)
        .all()
    )
    most_active = [
        {
            # student_number is now optional for newly registered accounts,
            # so fall back to email when it's not set.
            "student_number": r.student.student_number or r.student.email,
            "quizzes_completed": r.quizzes_completed,
        }
        for r in top
    ]

    subject_counts = Counter(q.subject for q in db.query(Quiz).all())
    most_studied = subject_counts.most_common(1)[0][0] if subject_counts else None

    return AdminDashboardOut(
        total_students=total_students,
        total_pdfs=total_pdfs,
        total_quizzes=total_quizzes,
        total_flashcards=total_flashcards,
        most_active_students=most_active,
        most_studied_subject=most_studied,
    )


@router.get("/students", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    return db.query(Student).order_by(Student.created_at.desc()).all()


@router.patch("/students/{student_id}/disable", response_model=StudentOut)
def disable_student(student_id: int, db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    student.is_active = False
    db.commit()
    db.refresh(student)
    return student


@router.patch("/students/{student_id}/enable", response_model=StudentOut)
def enable_student(student_id: int, db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    student.is_active = True
    db.commit()
    db.refresh(student)
    return student


@router.get("/uploads", response_model=list[PDFUploadOut])
def list_all_uploads(db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    return db.query(PDFUpload).order_by(PDFUpload.upload_date.desc()).all()


@router.delete("/uploads/{pdf_id}", status_code=204)
def delete_any_upload(pdf_id: int, db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    record = db.query(PDFUpload).filter(PDFUpload.pdf_id == pdf_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found.")
    Path(record.filepath).unlink(missing_ok=True)
    db.delete(record)
    db.commit()
    return None
