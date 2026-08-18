from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subject, Student
from app.schemas import SubjectOut, SubjectCreate
from app.security import get_current_student, require_admin

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# Seed subjects for BSCS come from the curriculum in the spec; BSIT is
# intentionally left for the administrator to populate.
_BSCS_SEED = {
    "First Semester": ["Introduction to Computing", "IPT 1: Computer Programming 1", "Living in the IT Era"],
    "Second Semester": ["IPT 2: Computer Programming 2", "Discrete Structures 1", "Human Computer Interaction 1"],
}


def ensure_seed_subjects(db: Session):
    existing = db.query(Subject).filter(Subject.course == "BSCS").count()
    if existing:
        return
    for semester, names in _BSCS_SEED.items():
        for name in names:
            db.add(Subject(course="BSCS", subject_name=name, semester=semester))
    db.commit()


@router.get("", response_model=list[SubjectOut])
def list_subjects(course: str = None, db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    ensure_seed_subjects(db)
    q = db.query(Subject)
    if course:
        q = q.filter(Subject.course == course.upper())
    return q.order_by(Subject.semester, Subject.subject_name).all()


@router.post("", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectCreate, db: Session = Depends(get_db),
                    _admin: Student = Depends(require_admin)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    for k, v in payload.model_dump().items():
        setattr(subject, k, v)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db), _admin: Student = Depends(require_admin)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found.")
    db.delete(subject)
    db.commit()
    return None
