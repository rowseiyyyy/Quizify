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

    insight = _build_insight(subject_perf, weekly_scores, accuracy, current_streak)

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


def _build_insight(subject_perf, weekly_scores, accuracy: float = 0.0,
                   current_streak: int = 0) -> str:
    """Personalized, actionable study advice — not just 'what to review'."""
    recent = [w["average_score"] for w in weekly_scores if w["average_score"] is not None]
    parts = []

    # 1. Trend + what it means
    if len(recent) >= 2:
        delta = recent[-1] - recent[0]
        if delta > 0:
            parts.append(f"Your scores improved {round(delta, 1)}% this week — momentum is on your side.")
        elif delta < 0:
            parts.append(f"Scores dipped {round(abs(delta), 1)}% this week — slow down and review before moving to new material.")
        else:
            parts.append("Your scores held steady this week.")
    else:
        parts.append("You're still building a score history — each quiz you finish makes this advice sharper.")

    # 2. Concrete action plan for the weakest subject
    if subject_perf:
        weakest = subject_perf[-1]
        if weakest["average_score"] < 75:
            parts.append(
                f"Focus plan for {weakest['subject']} (avg {weakest['average_score']}%): "
                "re-read that module, generate a 10-question quiz on it, drill flashcards on the "
                "questions you missed, then retake the quiz the next day to lock it in."
            )
        elif accuracy >= 85:
            strongest = subject_perf[0]
            parts.append(
                f"You're performing strongly ({accuracy}% overall). Keep {strongest['subject']} sharp with "
                "weekly review quizzes, and try 'Hard' difficulty to stretch yourself further."
            )
        else:
            parts.append(
                f"Good base ({accuracy}% overall). To push past {round(accuracy + 10)}%: after each quiz, "
                "turn every wrong answer into a flashcard and review it the next day — "
                "spaced repetition beats re-reading."
            )

    # 3. Study habit advice
    if current_streak >= 3:
        parts.append(f"Protect your {current_streak}-day streak: even one short 10-question quiz today keeps it alive.")
    else:
        parts.append("Aim for at least one quiz daily — consistent short sessions beat one long cram.")
    return " ".join(parts)
