from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, StreakRecord
from app.schemas import StudentRegister, StudentLogin, TokenOut, StudentOut, ForgotPasswordRequest
from app.security import hash_password, verify_password, create_access_token, get_current_student

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: StudentRegister, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    student = Student(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    db.add(StreakRecord(student_id=student.student_id))
    db.commit()

    token = create_access_token(student.student_id, student.is_admin)
    return TokenOut(access_token=token, student=StudentOut.model_validate(student))


@router.post("/login", response_model=TokenOut)
def login(payload: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == payload.email).first()
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not student.is_active:
        raise HTTPException(status_code=403, detail="This account has been disabled.")

    token = create_access_token(student.student_id, student.is_admin)
    return TokenOut(access_token=token, student=StudentOut.model_validate(student))


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # In production this would send a real email with a signed reset link.
    # We intentionally don't reveal whether the email exists, to avoid
    # leaking which emails are registered.
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.get("/me", response_model=StudentOut)
def me(current: Student = Depends(get_current_student)):
    return current
