"""Quick end-to-end smoke test using FastAPI's TestClient + a throwaway SQLite DB."""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./smoke_test.db"
sys.path.insert(0, ".")

# clean slate
if os.path.exists("smoke_test.db"):
    os.remove("smoke_test.db")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def check(label, resp, expect=200):
    ok = resp.status_code == expect
    print(f"[{'OK' if ok else 'FAIL'}] {label} -> {resp.status_code}")
    if not ok:
        print("    body:", resp.text[:500])
        raise SystemExit(1)
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


# 1. Register a student
r = check("register student", client.post("/auth/register", json={
    "full_name": "Juan Dela Cruz",
    "email": "juan@example.com",
    "password": "hunter22",
}), 201)
token = r["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   student_id:", r["student"]["student_id"])

# 2. Register an admin (manually flip is_admin via DB for the test)
check("register admin", client.post("/auth/register", json={
    "full_name": "Admin User",
    "email": "admin@example.com",
    "password": "adminpass",
}), 201)

from app.database import SessionLocal  # noqa: E402
from app.models import Student  # noqa: E402
db = SessionLocal()
admin = db.query(Student).filter(Student.email == "admin@example.com").first()
admin.is_admin = True
db.commit()
db.close()

r = check("login admin", client.post("/auth/login", json={"email": "admin@example.com", "password": "adminpass"}))
admin_headers = {"Authorization": f"Bearer {r['access_token']}"}

# 3. Login as student
r = check("login student", client.post("/auth/login", json={"email": "juan@example.com", "password": "hunter22"}))
assert r["student"]["full_name"] == "Juan Dela Cruz"

# 4. /auth/me
check("get me", client.get("/auth/me", headers=headers))

# 5. List subjects (seeds BSCS automatically)
r = check("list BSCS subjects", client.get("/subjects?course=BSCS", headers=headers))
assert len(r) == 6, f"expected 6 seeded BSCS subjects, got {len(r)}"

# 6. Admin adds a BSIT subject
r = check("admin add BSIT subject", client.post("/subjects", json={
    "course": "BSIT", "subject_name": "Platform Technologies", "semester": "First Semester"
}, headers=admin_headers), 201)
bsit_subject_id = r["subject_id"]

# Non-admin should be forbidden from adding subjects
check("non-admin blocked from adding subject", client.post("/subjects", json={
    "course": "BSIT", "subject_name": "Should Fail", "semester": "First Semester"
}, headers=headers), 403)

# 7. Upload a real PDF (built with reportlab for the test only)
from reportlab.pdfgen import canvas  # noqa: E402

sample_module_text = """
Introduction to Computing Module 3: Algorithms and Problem Solving

An algorithm is a step-by-step procedure for solving a problem or completing a task.
Computer programming involves writing algorithms that a computer can execute.
A variable is a named memory location used to store data that can change during program execution.
Hardware refers to the physical components of a computer system, such as the CPU and monitor.
Software is a set of instructions that tells a computer what tasks to perform.
Binary is a number system that uses only two digits, 0 and 1, to represent data.
The central processing unit, or CPU, is often called the brain of the computer.
A loop is a control structure that repeats a block of code while a condition remains true.
"""

pdf_path = "sample_module.pdf"
c = canvas.Canvas(pdf_path)
y = 800
for line in sample_module_text.strip().split("\n"):
    c.drawString(50, y, line.strip()[:100])
    y -= 20
    if y < 50:
        c.showPage()
        y = 800
c.save()

with open(pdf_path, "rb") as f:
    r = check("upload PDF", client.post(
        "/uploads",
        headers=headers,
        files={"file": ("sample_module.pdf", f, "application/pdf")},
        data={"subject": "Introduction to Computing"},
    ), 201)
pdf_id = r["pdf_id"]
print("   pdf status:", r["status"], "| page_count:", r["page_count"])
assert r["status"] == "ready"

# list uploads
r = check("list my uploads", client.get("/uploads", headers=headers))
assert len(r) == 1

# 8. Generate a quiz from the uploaded PDF (offline fallback generator, no GEMINI_API_KEY set)
r = check("generate quiz", client.post("/quizzes/generate", json={
    "pdf_id": pdf_id,
    "subject": "Introduction to Computing",
    "question_count": 5,
    "difficulty": "Medium",
    "question_types": ["Multiple Choice", "True or False", "Identification"],
}, headers=headers), 201)
quiz_id = r["quiz_id"]
questions = r["questions"]
assert len(questions) == 5
for q in questions:
    print("   Q:", q["question_type"], "-", q["question_text"][:70])

# 9. Submit answers (answer with the "correct" choice where we can guess, else first choice)
# We don't know the correct answers from the API response (as expected, to prevent cheating),
# so submit a mix of answers and just verify scoring works end-to-end.
answers = []
for q in questions:
    guess = q["choices"][0] if q["choices"] else "algorithm"
    answers.append({"question_id": q["question_id"], "answer": guess})

r = check("submit quiz", client.post(f"/quizzes/{quiz_id}/submit", json={
    "answers": answers, "time_taken_seconds": 305
}, headers=headers))
print("   score:", r["score"], "| correct:", r["correct_count"], "/", r["total"])

# Submitting twice should fail
check("re-submit blocked", client.post(f"/quizzes/{quiz_id}/submit", json={
    "answers": answers, "time_taken_seconds": 100
}, headers=headers), 400)

# 10. Quiz history
r = check("quiz history", client.get("/quizzes", headers=headers))
assert len(r) == 1 and r[0]["quiz_id"] == quiz_id

# 11. Generate flashcards
r = check("generate flashcards", client.post("/flashcards/generate", json={
    "pdf_id": pdf_id, "subject": "Introduction to Computing", "count": 4
}, headers=headers), 201)
assert len(r) == 4
fc_id = r[0]["flashcard_id"]
for fc in r:
    print("   FC front:", fc["front"][:60], "| back:", fc["back"][:60])

# 12. Mark a flashcard mastered + bookmarked
r = check("update flashcard", client.patch(f"/flashcards/{fc_id}", json={"mastered": True, "bookmarked": True}, headers=headers))
assert r["mastered"] is True and r["bookmarked"] is True

# 13. List flashcards filtered
r = check("list mastered flashcards", client.get("/flashcards?mastered=true", headers=headers))
assert len(r) == 1

# 14. Analytics
r = check("analytics", client.get("/analytics/me", headers=headers))
print("   analytics:", r["quizzes_completed"], "quizzes,", r["accuracy_rate"], "% accuracy, insight:", r["ai_insight"])

# 15. Admin dashboard
r = check("admin dashboard", client.get("/admin/dashboard", headers=admin_headers))
print("   admin dashboard:", r)
assert r["total_students"] == 2
assert r["total_pdfs"] == 1
assert r["total_quizzes"] == 1
assert r["total_flashcards"] == 4

# Non-admin blocked from admin dashboard
check("non-admin blocked from admin dashboard", client.get("/admin/dashboard", headers=headers), 403)

# 16. Admin can list/delete subject
check("admin delete BSIT subject", client.delete(f"/subjects/{bsit_subject_id}", headers=admin_headers), 204)

print("\\nALL SMOKE TESTS PASSED ✅")
