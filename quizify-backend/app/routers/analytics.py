from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Quiz, Flashcard, StreakRecord, Student
from app.schemas import AnalyticsOut
from app.security import get_current_student

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/me", response_model=AnalyticsOut)
def my_analytics(db: Session = Depends(get_db), current: Student = Depends(get_current_student)):
    since = datetime.utcnow() - timedelta(days=7)
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.student_id == current.student_id, Quiz.submitted == True)  # noqa: E712
        .all()
    )
    week_quizzes = [q for q in quizzes if q.submitted_at and q.submitted_at >= since]

    total_seconds = sum((q.time_taken_seconds or 0) for q in week_quizzes)
    weekly_hours = round(total_seconds / 3600, 2)

    accuracy = round(sum(q.score or 0 for q in quizzes) / len(quizzes), 1) if quizzes else 0.0

    flashcards_reviewed = (
        db.query(Flashcard)
        .filter(Flashcard.student_id == current.student_id, Flashcard.mastered == True)  # noqa: E712
        .count()
    )

    streak = db.query(StreakRecord).filter(StreakRecord.student_id == current.student_id).first()
    current_streak = streak.current_streak if streak else 0

    # subject performance
    by_subject = defaultdict(list)
    for q in quizzes:
        by_subject[q.subject].append(q.score or 0)
    subject_perf = [
        {"subject": s, "average_score": round(sum(v) / len(v), 1), "attempts": len(v)}
        for s, v in by_subject.items()
    ]
    subject_perf.sort(key=lambda x: -x["average_score"])
    strongest = subject_perf[0]["subject"] if subject_perf else None
    weakest = subject_perf[-1]["subject"] if subject_perf else None

    # weekly score trend (last 7 days, by day)
    weekly_scores = []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        day_scores = [q.score for q in quizzes if q.submitted_at and q.submitted_at.date() == day and q.score is not None]
        avg = round(sum(day_scores) / len(day_scores), 1) if day_scores else None
        weekly_scores.append({"date": day.isoformat(), "average_score": avg})

    insight = _build_insight(subject_perf, weekly_scores)

    return AnalyticsOut(
        weekly_study_hours=weekly_hours,
        quizzes_completed=len(quizzes),
        flashcards_reviewed=flashcards_reviewed,
        accuracy_rate=accuracy,
        current_streak=current_streak,
        strongest_subject=strongest,
        weakest_subject=weakest,
        subject_performance=subject_perf,
        weekly_scores=weekly_scores,
        ai_insight=insight,
    )


def _build_insight(subject_perf, weekly_scores) -> str:
    parts = []
    recent = [w["average_score"] for w in weekly_scores if w["average_score"] is not None]
    if len(recent) >= 2:
        delta = recent[-1] - recent[0]
        if delta > 0:
            parts.append(f"Your quiz scores have improved by {round(delta, 1)}% this week.")
        elif delta < 0:
            parts.append(f"Your quiz scores dipped by {round(abs(delta), 1)}% this week.")
    low_subjects = [s for s in subject_perf if s["average_score"] < 75]
    if low_subjects:
        weakest = low_subjects[-1]["subject"]
        parts.append(f"Consider reviewing {weakest} since your average score is below 75%.")
    if not parts:
        parts.append("Keep completing quizzes and flashcards to unlock personalized insights.")
    return " ".join(parts)
