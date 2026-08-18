from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Flashcard, PDFUpload, Student
from app.schemas import FlashcardGenerateRequest, FlashcardOut, FlashcardUpdateRequest
from app.security import get_current_student
from app.services.ai_service import generate_flashcards

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


@router.post("/generate", response_model=list[FlashcardOut], status_code=201)
def generate(payload: FlashcardGenerateRequest, db: Session = Depends(get_db),
             current: Student = Depends(get_current_student)):
    pdf = db.query(PDFUpload).filter(
        PDFUpload.pdf_id == payload.pdf_id, PDFUpload.student_id == current.student_id
    ).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF upload not found.")
    if pdf.status != "ready" or not pdf.extracted_text:
        raise HTTPException(status_code=400, detail="This PDF hasn't finished processing yet.")
    if not pdf.subject:
        raise HTTPException(status_code=400, detail="This PDF has no subject assigned.")

    subject = payload.subject or pdf.subject
    source_text = pdf.extracted_text

    generated = generate_flashcards(text=source_text, subject=subject, count=payload.count)
    if not generated:
        raise HTTPException(status_code=500, detail="Flashcard generation failed — please try again.")

    cards = []
    for g in generated:
        card = Flashcard(
            pdf_id=payload.pdf_id,
            student_id=current.student_id,
            subject=subject,
            front=g["front"],
            back=g["back"],
        )
        db.add(card)
        cards.append(card)
    db.commit()
    for c in cards:
        db.refresh(c)
    return cards


@router.get("", response_model=list[FlashcardOut])
def list_flashcards(subject: str = None, bookmarked: bool = None, mastered: bool = None,
                     search: str = None, db: Session = Depends(get_db),
                     current: Student = Depends(get_current_student)):
    q = db.query(Flashcard).filter(Flashcard.student_id == current.student_id)
    if subject:
        q = q.filter(Flashcard.subject == subject)
    if bookmarked is not None:
        q = q.filter(Flashcard.bookmarked == bookmarked)
    if mastered is not None:
        q = q.filter(Flashcard.mastered == mastered)
    if search:
        like = f"%{search}%"
        q = q.filter((Flashcard.front.ilike(like)) | (Flashcard.back.ilike(like)))
    return q.order_by(Flashcard.created_at.desc()).all()


@router.patch("/{flashcard_id}", response_model=FlashcardOut)
def update_flashcard(flashcard_id: int, payload: FlashcardUpdateRequest, db: Session = Depends(get_db),
                      current: Student = Depends(get_current_student)):
    card = db.query(Flashcard).filter(
        Flashcard.flashcard_id == flashcard_id, Flashcard.student_id == current.student_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found.")
    if payload.mastered is not None:
        card.mastered = payload.mastered
    if payload.bookmarked is not None:
        card.bookmarked = payload.bookmarked
    db.commit()
    db.refresh(card)
    return card
