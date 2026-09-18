# Quizify

An AI-powered study reviewer that turns lecture PDFs into interactive quizzes and flashcards, built for first-year BSCS & BSIT students.

Upload a module, and Quizify extracts the text, generates practice quizzes and flashcards (via Google Gemini, with an offline fallback generator), tracks your study streaks, and surfaces analytics on how you're performing per subject.

## Key Features

- **PDF to practice material** — upload a lecture PDF (up to 30 MB); text is extracted with `pdfplumber` and cleaned automatically
- **AI quiz generation** — multiple-choice, true/false, and identification questions; answers are graded server-side and never exposed to the client before submission
- **Flashcards** — auto-generated from your PDFs, with mastered/bookmarked tracking and filtering
- **Study streaks** — daily streak tracking that resets if you miss a day
- **Analytics** — weekly study hours, accuracy, per-subject performance, and an AI-generated study insight
- **Accounts & roles** — JWT authentication with bcrypt-hashed passwords; admin panel for managing students, subjects, and uploads
- **Curriculum-aware subjects** — BSCS subjects are pre-seeded; BSIT subjects are admin-managed

## Technology Stack

| Layer | Choice |
|---|---|
| Backend | Python 3, FastAPI |
| Database | SQLAlchemy 2.0 (SQLite by default; MySQL and PostgreSQL supported via `DATABASE_URL`) |
| Auth | PyJWT + passlib/bcrypt |
| PDF parsing | pdfplumber |
| AI generation | Google Gemini (OpenAI-compatible endpoint), with a built-in offline heuristic fallback |
| Frontend | Single-file vanilla HTML/CSS/JS app (`index.html`), served by the API at `/` |

## Getting Started

Requires Python 3.10+.

```bash
# from the repository root
cd quizify-backend

python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)

pip install -r requirements.txt

copy .env.example .env         # defaults work out of the box (SQLite)

uvicorn app.main:app --reload --port 8000
```

Then open:

- **http://localhost:8000** — the Quizify web app
- **http://localhost:8000/docs** — interactive Swagger API docs

To verify the full pipeline (register → upload → generate → submit → analytics), run:

```bash
python smoke_test.py
```

### Optional: AI generation

Quiz generation works with zero API keys via the offline fallback generator. To enable real AI-generated content, get a free key at [Google AI Studio](https://aistudio.google.com/apikey) and set `GEMINI_API_KEY` in `.env`.


## Environment Variables

All variables are optional and have working defaults (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./quizify.db` | SQLAlchemy connection URL (SQLite, MySQL, or PostgreSQL) |
| `JWT_SECRET` | dev fallback | Secret used to sign JWTs — set a strong random value in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifetime (24 h) |
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio key; empty enables the offline fallback |
| `GEMINI_MODEL` | `gemini-flash-latest` | Gemini model used for generation |
| `GEMINI_BASE_URL` | Google endpoint | OpenAI-compatible base URL (point at Ollama/vLLM for local LLMs) |
| `UPLOAD_DIR` | `./uploads` | Directory where uploaded PDFs are stored |
| `MAX_UPLOAD_MB` | `30` | Maximum upload size |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

## Project Structure

```
quizify-backend/           # FastAPI application
├── app/
│   ├── main.py            # App entry point, static frontend mount, /health
│   ├── config.py          # Environment-driven settings
│   ├── database.py        # SQLAlchemy engine/session
│   ├── models.py          # ORM models (students, subjects, uploads, quizzes, flashcards, streaks)
│   ├── schemas.py         # Pydantic request/response models
│   ├── security.py        # JWT + bcrypt + auth dependencies
│   ├── services/
│   │   ├── pdf_service.py     # PDF text extraction + cleaning
│   │   └── ai_service.py      # Quiz/flashcard generation (Gemini or offline fallback)
│   └── routers/
│       ├── auth.py, subjects.py, uploads.py, quizzes.py,
│       └── flashcards.py, analytics.py, admin.py
├── static/                # Served at "/" (index.html + logo.png)
├── schema.sql             # Reference SQL DDL
├── smoke_test.py          # End-to-end test (25 assertions)
├── requirements.txt
└── .env.example
index.html                 # Frontend source (copied into static/ for serving)
Procfile                   # Start command for Railway
```

## API Overview

Full interactive documentation is available at `/docs` (Swagger UI). Main route groups:

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET/POST /subjects`, `PUT/DELETE /subjects/{id}` *(admin)*
- `POST/GET /uploads`, `DELETE /uploads/{id}`
- `POST /quizzes/generate`, `GET /quizzes/{id}`, `POST /quizzes/{id}/submit`, `GET /quizzes`
- `POST /flashcards/generate`, `GET /flashcards`, `PATCH /flashcards/{id}`
- `GET /analytics/me`
- `GET /admin/dashboard`, `GET /admin/students`, `PATCH /admin/students/{id}/disable|enable`, `GET/DELETE /admin/uploads` *(admin)*

All endpoints except registration, login, and forgot-password require a bearer token.

## Deployment

The repository includes a `Procfile` with a production-ready start command (`uvicorn --host 0.0.0.0 --port $PORT`), so it deploys directly to Railway (or any platform that honors Procfiles and injects `PORT`). Set the environment variables above in your platform's dashboard; the database tables are created automatically on first boot.

## Project Status

**v1.0.0 — First Public Release**

The application is feature-complete for its academic scope and covered by an automated end-to-end smoke test.

## Future Development

Planned improvements:

- Transactional email for password resets (`/auth/forgot-password` is currently a stub)
- Rate limiting / brute-force protection on login
- Object storage (S3/Cloudinary) for uploaded PDFs instead of local disk
- Background job queue for async generation of very large PDFs
- Alembic migrations for evolving the database schema
- Admin promotion workflow (currently a database-level flag)

## License

This project does not currently ship with an open-source license. All rights are reserved by the author — you may view the source, but reuse, redistribution, and modification require permission. (If you intend to publish under an open license, add a `LICENSE` file — MIT or Apache-2.0 are common choices.)
