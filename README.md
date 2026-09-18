# Quizify

An AI-powered study reviewer that turns lecture PDFs into interactive quizzes and flashcards, built for first-year BSCS and BSIT students.

Upload a module, and Quizify extracts the text, generates practice quizzes and flashcards using Google Gemini with an offline fallback generator, tracks study streaks, and provides analytics on performance by subject.

## Key Features

* **PDF to Practice Material** — Upload lecture PDFs up to 30 MB. Text is extracted using `pdfplumber` and cleaned automatically.
* **AI Quiz Generation** — Generate multiple-choice, true/false, and identification questions. Answers are graded server-side and are not exposed to the client before submission.
* **Flashcards** — Automatically generate flashcards from uploaded PDFs, with mastered/bookmarked tracking and filtering.
* **Study Streaks** — Track daily study streaks that reset when a day is missed.
* **Analytics** — View weekly study hours, accuracy, per-subject performance, and AI-generated study insights.
* **Accounts & Roles** — JWT authentication with bcrypt-hashed passwords and an admin panel for managing students, subjects, and uploads.
* **Curriculum-Aware Subjects** — BSCS subjects are pre-seeded, while BSIT subjects are managed by administrators.

## Technology Stack

| Layer          | Technology                                    |
| -------------- | --------------------------------------------- |
| Backend        | Python 3, FastAPI                             |
| Database       | SQLAlchemy 2.0, SQLite, MySQL, PostgreSQL     |
| Authentication | PyJWT, Passlib, bcrypt                        |
| PDF Processing | pdfplumber                                    |
| AI Generation  | Google Gemini with OpenAI-compatible endpoint |
| AI Fallback    | Built-in offline heuristic generator          |
| Frontend       | Vanilla HTML, CSS, and JavaScript             |
| Deployment     | Railway                                       |

## Getting Started

### Prerequisites

* Python 3.10 or higher
* Git
* SQLite, MySQL, or PostgreSQL

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project
cd quizify-backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Configuration

Create your environment file:

```bash
copy .env.example .env
```

For macOS/Linux:

```bash
cp .env.example .env
```

The default configuration uses SQLite and can run without an AI API key through the built-in offline fallback.

### Run the Application

```bash
uvicorn app.main:app --reload --port 8000
```

The application will be available at:

**Web Application:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

### Run the Smoke Test

To verify the main application workflow:

```bash
python smoke_test.py
```

The smoke test covers the core pipeline from registration and module upload through quiz generation, submission, and analytics.

## AI Generation

Quizify can generate study materials using Google Gemini.

AI generation is optional. Without an API key, Quizify uses its built-in offline fallback generator.

To enable Gemini:

1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Add the key to your `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

## Environment Variables

| Variable                      | Default                  | Purpose                          |
| ----------------------------- | ------------------------ | -------------------------------- |
| `DATABASE_URL`                | `sqlite:///./quizify.db` | Database connection URL          |
| `JWT_SECRET`                  | Development fallback     | Secret used to sign JWTs         |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                   | Access token lifetime            |
| `GEMINI_API_KEY`              | Empty                    | Google AI Studio API key         |
| `GEMINI_MODEL`                | `gemini-flash-latest`    | Gemini model used for generation |
| `GEMINI_BASE_URL`             | Google endpoint          | OpenAI-compatible AI endpoint    |
| `UPLOAD_DIR`                  | `./uploads`              | Uploaded PDF storage directory   |
| `MAX_UPLOAD_MB`               | `30`                     | Maximum PDF upload size          |
| `CORS_ORIGINS`                | `*`                      | Allowed CORS origins             |

For production deployments, use a strong `JWT_SECRET` and configure the appropriate database and CORS settings.

## Project Structure

```text
quizify-backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   ├── services/
│   │   ├── pdf_service.py
│   │   └── ai_service.py
│   └── routers/
│       ├── auth.py
│       ├── subjects.py
│       ├── uploads.py
│       ├── quizzes.py
│       ├── flashcards.py
│       ├── analytics.py
│       └── admin.py
├── static/
├── schema.sql
├── smoke_test.py
├── requirements.txt
├── .env.example
├── index.html
├── Procfile
└── README.md
```

## API Overview

Interactive API documentation is available through FastAPI's Swagger UI:

`http://localhost:8000/docs`

### Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Subjects

```text
GET    /subjects
POST   /subjects
PUT    /subjects/{id}
DELETE /subjects/{id}
```

### Uploads

```text
POST   /uploads
GET    /uploads
DELETE /uploads/{id}
```

### Quizzes

```text
POST /quizzes/generate
GET  /quizzes/{id}
POST /quizzes/{id}/submit
GET  /quizzes
```

### Flashcards

```text
POST  /flashcards/generate
GET   /flashcards
PATCH /flashcards/{id}
```

### Analytics

```text
GET /analytics/me
```

### Administration

```text
GET    /admin/dashboard
GET    /admin/students
PATCH  /admin/students/{id}/disable
PATCH  /admin/students/{id}/enable
GET    /admin/uploads
DELETE /admin/uploads
```

Authenticated endpoints require a valid bearer token unless otherwise specified.

## Deployment

Quizify includes a `Procfile` configured for deployment on Railway and other platforms that support Procfiles and provide a `PORT` environment variable.

The production server runs using:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the required environment variables through the deployment platform's settings.

## Project Status

### v1.0.0 — First Public Release

Quizify v1.0.0 is the first public release of the project.

The current release provides the core functionality for uploading learning materials, generating quizzes and flashcards, managing subjects, tracking study activity, and viewing performance analytics.

## Future Development

Potential improvements include:

* Transactional email for password resets
* Rate limiting and brute-force protection
* Object storage for uploaded PDFs
* Background processing for large PDF generation tasks
* Alembic database migrations
* Improved admin promotion workflow

## License

This project does not currently include an open-source license.

All rights are reserved by the author. Viewing the source code does not grant permission to reuse, redistribute, or modify the project.

If an open-source license is added in the future, the repository will include a corresponding `LICENSE` file.
