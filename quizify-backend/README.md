# Quizify — Backend API

A FastAPI backend for **Quizify**, the AI-powered reviewer for first-year BSCS & BSIT students.
It implements the full data model, JWT authentication, real PDF text extraction, AI-driven quiz
and flashcard generation, streak tracking, study analytics, and an
admin panel — matching the frontend prototype delivered earlier.

## Stack

| Layer          | Choice                                                              |
|----------------|----------------------------------------------------------------------|
| Framework      | FastAPI                                                              |
| ORM / DB       | SQLAlchemy — SQLite by default, MySQL in production (one env var)   |
| Auth           | JWT (PyJWT) + bcrypt password hashing                                |
| PDF parsing    | pdfplumber                                                           |
| AI generation  | OpenAI API if `OPENAI_API_KEY` is set, otherwise a built-in offline heuristic generator |

## Why an offline AI fallback?

The spec calls for "OpenAI API **or** a local LLM." To make sure the project runs and is fully
demoable/gradable with zero external dependencies or API costs, `app/services/ai_service.py`
ships with a deterministic, rule-based generator (keyword extraction + sentence-based
question/flashcard construction) that activates automatically whenever `OPENAI_API_KEY` is
empty. Set the key and it seamlessly switches to real LLM-generated questions and flashcards —
no code changes needed either way.

## Quick start (SQLite, zero setup)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # defaults already work out of the box
uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000/docs** for interactive Swagger docs (every endpoint below is
callable directly from there).

Run the automated end-to-end test any time with:

```bash
python3 smoke_test.py
```

It registers a student and an admin, uploads a real PDF, generates a quiz from the extracted
text, submits answers, checks streak/analytics, and verifies admin-only routes are
protected — 25 assertions, all against a throwaway SQLite file.

## Switching to MySQL

1. Create the database (see `schema.sql` for the reference DDL, or just let SQLAlchemy create
   it automatically on first run).
2. In `.env`, set:
   ```
   DATABASE_URL=mysql+pymysql://quizify_user:password@localhost:3306/quizify
   ```
3. Restart the app — tables are created automatically via `Base.metadata.create_all`.

## Enabling real AI generation

Set in `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
To use a local/self-hosted LLM instead, point `OPENAI_BASE_URL` at any OpenAI-compatible
endpoint (e.g. Ollama's `/v1`, vLLM, LM Studio) — the request/response shape is unchanged.

## Authentication

All endpoints except `/auth/register`, `/auth/login`, and `/auth/forgot-password` require a
bearer token:
```
Authorization: Bearer <access_token>
```
Admin-only endpoints additionally check `is_admin` on the student record. There's no separate
admin login route — an admin is just a student row with `is_admin = true` (flip it directly in
the DB, or expose an internal promotion route if you need one for your deployment).

## Endpoints

| Method | Path                              | Description                                    |
|--------|-----------------------------------|--------------------------------------------------|
| POST   | `/auth/register`                  | Create a student account (`full_name`, `email`, `password`), returns a JWT |
| POST   | `/auth/login`                     | Log in with email + password                      |
| POST   | `/auth/forgot-password`           | Stub — always returns a generic success message   |
| GET    | `/auth/me`                        | Current logged-in student                         |
| GET    | `/subjects?course=BSCS`           | List subjects (BSCS is seeded; BSIT is admin-managed) |
| POST   | `/subjects`                       | *(admin)* Add a subject                           |
| PUT    | `/subjects/{id}`                  | *(admin)* Edit a subject                          |
| DELETE | `/subjects/{id}`                  | *(admin)* Remove a subject                        |
| POST   | `/uploads`                        | Upload a PDF (multipart, ≤30MB) — extracts text immediately |
| GET    | `/uploads`                        | List my uploads                                   |
| GET    | `/uploads/{id}`                   | Get one upload                                     |
| DELETE | `/uploads/{id}`                   | Delete my upload                                   |
| POST   | `/quizzes/generate`               | Generate a quiz from a `pdf_id` or bare subject    |
| GET    | `/quizzes/{id}`                   | Fetch a quiz (questions only — no answers exposed) |
| POST   | `/quizzes/{id}/submit`            | Submit answers, get score + feedback + streak update |
| GET    | `/quizzes`                        | My quiz history (submitted quizzes only)           |
| POST   | `/flashcards/generate`            | Generate flashcards from a `pdf_id` or bare subject |
| GET    | `/flashcards?subject=&mastered=&bookmarked=&search=` | List/filter my flashcards        |
| PATCH  | `/flashcards/{id}`                | Mark mastered / bookmarked                         |
| GET    | `/analytics/me`                   | Weekly hours, accuracy, subject performance, AI insight |
| GET    | `/admin/dashboard`                | *(admin)* Platform-wide totals                     |
| GET    | `/admin/students`                 | *(admin)* List all students                        |
| PATCH  | `/admin/students/{id}/disable`    | *(admin)* Disable an account                       |
| PATCH  | `/admin/students/{id}/enable`     | *(admin)* Re-enable an account                     |
| GET    | `/admin/uploads`                  | *(admin)* List every uploaded PDF                  |
| DELETE | `/admin/uploads/{id}`             | *(admin)* Delete any PDF                           |

## Notable design decisions

- **No answer leakage**: `GET /quizzes/{id}` returns questions and choices but never
  `correct_answer` — grading happens server-side on submit.
- **Streaks**: computed transactionally on submit — a quiz submitted on a new calendar day
  extends the streak, a gap of more than one day resets it to 1, matching the spec ("missing one
  day resets the streak").
- **Graceful AI degradation**: if `OPENAI_API_KEY` is set but the API call fails (rate limit,
  network error, bad response), the app automatically falls back to the offline generator rather
  than returning a 500 to the student.
- **BSIT subjects**: intentionally start empty (per the spec) and are fully admin-manageable via
  the `/subjects` CRUD endpoints; BSCS subjects are auto-seeded from the given curriculum.

## Project layout

```
app/
  main.py              FastAPI app, router registration, table creation
  config.py            Environment-driven settings
  database.py          SQLAlchemy engine/session
  models.py             ORM models (students, subjects, uploads, quizzes, flashcards, streaks)
  schemas.py            Pydantic request/response models
  security.py            JWT + bcrypt + auth dependencies
  services/
    pdf_service.py       PDF text extraction + cleaning + keyword extraction
    ai_service.py         Quiz/flashcard generation (OpenAI or offline fallback)
  routers/
    auth.py, subjects.py, uploads.py, quizzes.py, flashcards.py,
    analytics.py, admin.py
schema.sql              Reference MySQL DDL
requirements.txt
.env.example
smoke_test.py           25-assertion end-to-end test
```

## What's left for a production deployment

- Real transactional email for `/auth/forgot-password` (currently a stub).
- Rate limiting / brute-force protection on `/auth/login`.
- Object storage (S3/Cloudinary) instead of local disk for uploaded PDFs at scale.
- An admin "promote to admin" endpoint or a separate seed script (currently done by hand in the DB).
- Background job queue (e.g. Celery/RQ) if quiz/flashcard generation needs to be async for very
  large PDFs — right now generation happens synchronously within the request.
