import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # --- Database ---------------------------------------------------------
    # Default is SQLite so the project runs out of the box with zero setup.
    # For production, set DATABASE_URL to a MySQL DSN, e.g.:
    #   mysql+pymysql://quizify_user:password@localhost:3306/quizify
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'quizify.db'}")

    # --- Auth ---------------------------------------------------------------
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

    # --- AI -----------------------------------------------------------------
    # If OPENAI_API_KEY is set, the AI service calls the real OpenAI API.
    # Otherwise it falls back to a deterministic, offline heuristic generator
    # so the whole pipeline still works with zero external dependencies.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # --- Uploads --------------------------------------------------------------
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "30"))

    # --- CORS -----------------------------------------------------------------
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
