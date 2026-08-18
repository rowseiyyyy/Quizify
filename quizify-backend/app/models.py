import enum
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, Date, ForeignKey, Float, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class CourseEnum(str, enum.Enum):
    BSCS = "BSCS"
    BSIT = "BSIT"


class DifficultyEnum(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    MIXED = "Mixed"


class QuestionTypeEnum(str, enum.Enum):
    MULTIPLE_CHOICE = "Multiple Choice"
    TRUE_FALSE = "True or False"
    IDENTIFICATION = "Identification"


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------
class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), unique=True, index=True, nullable=True)
    full_name = Column(String(120), nullable=False)
    course = Column(String(10), nullable=True)  # BSCS | BSIT (optional)
    year_level = Column(String(20), nullable=True, default="1st Year")
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pdf_uploads = relationship("PDFUpload", back_populates="student", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="student", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="student", cascade="all, delete-orphan")
    streak = relationship("StreakRecord", back_populates="student", uselist=False, cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Subject (admin-manageable, especially for BSIT)
# ---------------------------------------------------------------------------
class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, index=True)
    course = Column(String(10), nullable=False)  # BSCS | BSIT
    subject_name = Column(String(150), nullable=False)
    semester = Column(String(30), nullable=True)  # e.g. "First Semester"

    __table_args__ = (UniqueConstraint("course", "subject_name", name="uq_course_subject"),)


# ---------------------------------------------------------------------------
# PDF Upload
# ---------------------------------------------------------------------------
class PDFUpload(Base):
    __tablename__ = "pdf_uploads"

    pdf_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    subject = Column(String(150), nullable=True)
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    status = Column(String(30), default="uploaded")  # uploaded -> processing -> ready -> failed
    upload_date = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="pdf_uploads")
    quizzes = relationship("Quiz", back_populates="pdf", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="pdf", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Quiz + Quiz Questions
# ---------------------------------------------------------------------------
class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_uploads.pdf_id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    subject = Column(String(150), nullable=False)
    difficulty = Column(String(20), nullable=False, default=DifficultyEnum.MEDIUM.value)
    question_types = Column(JSON, default=list)
    question_count = Column(Integer, default=10)

    # Filled in once the quiz is submitted:
    score = Column(Float, nullable=True)          # percentage
    correct_count = Column(Integer, nullable=True)
    wrong_count = Column(Integer, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    submitted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="quizzes")
    pdf = relationship("PDFUpload", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    question_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"), nullable=False)
    order_index = Column(Integer, default=0)
    question_type = Column(String(30), default=QuestionTypeEnum.MULTIPLE_CHOICE.value)
    question_text = Column(Text, nullable=False)
    choices = Column(JSON, nullable=True)         # list[str], null for identification
    correct_answer = Column(String(500), nullable=False)
    student_answer = Column(String(500), nullable=True)
    is_correct = Column(Boolean, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------
class Flashcard(Base):
    __tablename__ = "flashcards"

    flashcard_id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_uploads.pdf_id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    subject = Column(String(150), nullable=False)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    mastered = Column(Boolean, default=False)
    bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="flashcards")
    pdf = relationship("PDFUpload", back_populates="flashcards")


# ---------------------------------------------------------------------------
# Streak aggregate (current streak, average score, quizzes completed)
# ---------------------------------------------------------------------------
class StreakRecord(Base):
    __tablename__ = "streaks"

    student_id = Column(Integer, ForeignKey("students.student_id"), primary_key=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_quiz_date = Column(Date, nullable=True)
    average_score = Column(Float, default=0.0)
    quizzes_completed = Column(Integer, default=0)

    student = relationship("Student", back_populates="streak")
