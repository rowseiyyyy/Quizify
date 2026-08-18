from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


# ================= Auth / Students =================
class StudentRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class StudentOut(BaseModel):
    student_id: int
    student_number: Optional[str] = None
    full_name: str
    course: Optional[str] = None
    year_level: Optional[str] = None
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentOut


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# ================= Subjects =================
class SubjectCreate(BaseModel):
    course: str = Field(pattern="^(BSCS|BSIT)$")
    subject_name: str
    semester: Optional[str] = None


class SubjectOut(BaseModel):
    subject_id: int
    course: str
    subject_name: str
    semester: Optional[str]

    class Config:
        from_attributes = True


# ================= PDF Upload =================
class PDFUploadOut(BaseModel):
    pdf_id: int
    filename: str
    subject: Optional[str]
    status: str
    page_count: int
    size_bytes: int
    upload_date: datetime

    class Config:
        from_attributes = True


# ================= Quiz =================
class QuizGenerateRequest(BaseModel):
    pdf_id: int
    subject: Optional[str] = None
    question_count: int = Field(default=10, ge=1, le=50)
    difficulty: str = Field(default="Medium", pattern="^(Easy|Medium|Hard|Mixed)$")
    question_types: List[str] = Field(default_factory=lambda: ["Multiple Choice"])


class QuizQuestionOut(BaseModel):
    question_id: int
    order_index: int
    question_type: str
    question_text: str
    choices: Optional[List[str]]

    class Config:
        from_attributes = True


class QuizOut(BaseModel):
    quiz_id: int
    subject: str
    difficulty: str
    question_count: int
    submitted: bool
    score: Optional[float]
    correct_count: Optional[int]
    wrong_count: Optional[int]
    time_taken_seconds: Optional[int]
    created_at: datetime
    questions: List[QuizQuestionOut]

    class Config:
        from_attributes = True


class QuizAnswer(BaseModel):
    question_id: int
    answer: str


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]
    time_taken_seconds: int


class QuizResultOut(BaseModel):
    quiz_id: int
    score: float
    correct_count: int
    wrong_count: int
    total: int
    time_taken_seconds: int
    feedback: str
    review_recommendations: List[str]


class QuizHistoryOut(BaseModel):
    quiz_id: int
    subject: str
    difficulty: str
    question_count: int
    score: Optional[float]
    time_taken_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ================= Flashcards =================
class FlashcardGenerateRequest(BaseModel):
    pdf_id: int
    subject: Optional[str] = None
    count: int = Field(default=10, ge=1, le=50)


class FlashcardOut(BaseModel):
    flashcard_id: int
    subject: str
    front: str
    back: str
    mastered: bool
    bookmarked: bool

    class Config:
        from_attributes = True


class FlashcardUpdateRequest(BaseModel):
    mastered: Optional[bool] = None
    bookmarked: Optional[bool] = None


# ================= Analytics =================
class AnalyticsOut(BaseModel):
    weekly_study_hours: float
    quizzes_completed: int
    flashcards_reviewed: int
    accuracy_rate: float
    current_streak: int
    strongest_subject: Optional[str]
    weakest_subject: Optional[str]
    subject_performance: List[dict]
    weekly_scores: List[dict]
    ai_insight: str


# ================= Admin =================
class AdminDashboardOut(BaseModel):
    total_students: int
    total_pdfs: int
    total_quizzes: int
    total_flashcards: int
    most_active_students: List[dict]
    most_studied_subject: Optional[str]
