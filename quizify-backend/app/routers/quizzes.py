from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Quiz, QuizQuestion, PDFUpload, Student, StreakRecord
from app.schemas import (
    QuizGenerateRequest, QuizOut, QuizSubmitRequest, QuizResultOut, QuizHistoryOut
)
from app.security import get_current_student
from app.services.ai_service import generate_quiz

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/generate", response_model=QuizOut, status_code=201)
def generate(payload: QuizGenerateRequest, db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
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

    generated = generate_quiz(
        text=source_text,
        subject=subject,
        question_count=payload.question_count,
        difficulty=payload.difficulty,
        question_types=payload.question_types,
    )
    if not generated:
        raise HTTPException(status_code=500, detail="Quiz generation failed — please try again.")

    quiz = Quiz(
        pdf_id=payload.pdf_id,
        student_id=current.student_id,
        subject=subject,
        difficulty=payload.difficulty,
        question_types=payload.question_types,
        question_count=len(generated),
    )
    db.add(quiz)
    db.flush()

    for i, q in enumerate(generated):
        db.add(QuizQuestion(
            quiz_id=quiz.quiz_id,
            order_index=i,
            question_type=q.get("question_type", "Multiple Choice"),
            question_text=q["question_text"],
            choices=q.get("choices"),
            correct_answer=str(q["correct_answer"]),
        ))
    db.commit()
    db.refresh(quiz)
    return quiz


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id, Quiz.student_id == current.student_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizResultOut)
def submit_quiz(quiz_id: int, payload: QuizSubmitRequest, db: Session = Depends(get_db),
                 current: Student = Depends(get_current_student)):
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id, Quiz.student_id == current.student_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    if quiz.submitted:
        raise HTTPException(status_code=400, detail="This quiz has already been submitted.")

    answer_map = {a.question_id: a.answer for a in payload.answers}
    correct = 0
    wrong_topics = []
    for question in quiz.questions:
        given = answer_map.get(question.question_id)
        question.student_answer = given
        is_correct = (given is not None and given.strip().lower() == question.correct_answer.strip().lower())
        question.is_correct = is_correct
        if is_correct:
            correct += 1
        else:
            wrong_topics.append(question.question_text[:40])

    total = len(quiz.questions)
    wrong = total - correct
    score_pct = round((correct / total) * 100, 1) if total else 0.0

    quiz.correct_count = correct
    quiz.wrong_count = wrong
    quiz.score = score_pct
    quiz.time_taken_seconds = payload.time_taken_seconds
    quiz.submitted = True
    quiz.submitted_at = datetime.utcnow()
    db.commit()

    _update_streak_and_stats(db, current, score_pct)

    if score_pct >= 85:
        feedback = "Excellent! You understand the topic very well."
    elif score_pct >= 70:
        feedback = "Good job! Solid grasp overall — a bit more review will get you to mastery."
    else:
        feedback = "Keep practicing! Review the recommended topics and try again."

    return QuizResultOut(
        quiz_id=quiz.quiz_id,
        score=score_pct,
        correct_count=correct,
        wrong_count=wrong,
        total=total,
        time_taken_seconds=payload.time_taken_seconds,
        feedback=feedback,
        review_recommendations=wrong_topics[:3],
    )


def _update_streak_and_stats(db: Session, student: Student, score_pct: float):
    record = db.query(StreakRecord).filter(StreakRecord.student_id == student.student_id).first()
    if not record:
        record = StreakRecord(student_id=student.student_id)
        db.add(record)
        db.flush()

    today = date.today()
    if record.last_quiz_date == today:
        pass  # already studied today, streak unchanged
    elif record.last_quiz_date == today - timedelta(days=1):
        record.current_streak += 1
    else:
        record.current_streak = 1  # missed a day (or first ever quiz) -> streak resets/starts
    record.longest_streak = max(record.longest_streak, record.current_streak)
    record.last_quiz_date = today

    total_before = record.quizzes_completed
    record.average_score = round(
        ((record.average_score * total_before) + score_pct) / (total_before + 1), 1
    )
    record.quizzes_completed += 1
    db.commit()


@router.get("", response_model=list[QuizHistoryOut])
def quiz_history(db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    return (
        db.query(Quiz)
        .filter(Quiz.student_id == current.student_id, Quiz.submitted == True)  # noqa: E712
        .order_by(Quiz.submitted_at.desc())
        .all()
    )
