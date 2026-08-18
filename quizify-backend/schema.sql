-- Reference MySQL schema for Quizify.
-- SQLAlchemy will actually create these tables automatically on first run
-- (see app/main.py -> Base.metadata.create_all), so running this file by
-- hand is optional. It's provided so the schema can be reviewed, diagrammed,
-- or handed to a DBA independently of the ORM.

CREATE DATABASE IF NOT EXISTS quizify CHARACTER SET utf8mb4;
USE quizify;

CREATE TABLE students (
  student_id      INT AUTO_INCREMENT PRIMARY KEY,
  student_number  VARCHAR(20) NULL UNIQUE,          -- optional (no longer collected at registration)
  full_name       VARCHAR(120) NOT NULL,
  course          VARCHAR(10) NULL,                 -- BSCS | BSIT (optional)
  year_level      VARCHAR(20) NULL DEFAULT '1st Year',  -- optional
  email           VARCHAR(150) NOT NULL UNIQUE,
  password_hash   VARCHAR(255) NOT NULL,
  is_admin        BOOLEAN DEFAULT FALSE,
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================================
-- MIGRATION QUERIES (for an existing database)
-- ---------------------------------------------------------------------------
-- MySQL / MariaDB: make student_number, course, and year_level nullable so
-- that new registrations (which no longer collect these fields) can be saved.
-- Existing rows are preserved.
--
--   ALTER TABLE students
--     MODIFY student_number VARCHAR(20) NULL UNIQUE,
--     MODIFY course         VARCHAR(10) NULL,
--     MODIFY year_level     VARCHAR(20) NULL DEFAULT '1st Year';
--
-- SQLite: SQLite does not support ALTER COLUMN. Rebuild the table instead:
--
--   PRAGMA foreign_keys=OFF;
--   BEGIN TRANSACTION;
--   ALTER TABLE students RENAME TO students_old;
--   CREATE TABLE students (
--     student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
--     student_number  VARCHAR(20) UNIQUE,
--     full_name       VARCHAR(120) NOT NULL,
--     course          VARCHAR(10),
--     year_level      VARCHAR(20) DEFAULT '1st Year',
--     email           VARCHAR(150) NOT NULL UNIQUE,
--     password_hash   VARCHAR(255) NOT NULL,
--     is_admin        BOOLEAN DEFAULT FALSE,
--     is_active       BOOLEAN DEFAULT TRUE,
--     created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
--   );
--   INSERT INTO students (student_id, student_number, full_name, course, year_level, email, password_hash, is_admin, is_active, created_at)
--     SELECT student_id, student_number, full_name, course, year_level, email, password_hash, is_admin, is_active, created_at FROM students_old;
--   DROP TABLE students_old;
--   COMMIT;
--   PRAGMA foreign_keys=ON;
--
-- If you want to fully DROP the columns instead (only after confirming no
-- existing code or reports depend on them):
--
--   ALTER TABLE students DROP COLUMN course;
--   ALTER TABLE students DROP COLUMN year_level;
--   ALTER TABLE students DROP COLUMN student_number;
-- ===========================================================================

CREATE TABLE subjects (
  subject_id    INT AUTO_INCREMENT PRIMARY KEY,
  course        VARCHAR(10) NOT NULL,
  subject_name  VARCHAR(150) NOT NULL,
  semester      VARCHAR(30),
  UNIQUE KEY uq_course_subject (course, subject_name)
);

CREATE TABLE pdf_uploads (
  pdf_id          INT AUTO_INCREMENT PRIMARY KEY,
  student_id      INT NOT NULL,
  filename        VARCHAR(255) NOT NULL,
  filepath        VARCHAR(500) NOT NULL,
  subject         VARCHAR(150),
  extracted_text  LONGTEXT,
  page_count      INT DEFAULT 0,
  size_bytes      INT DEFAULT 0,
  status          VARCHAR(30) DEFAULT 'uploaded',
  upload_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE quizzes (
  quiz_id             INT AUTO_INCREMENT PRIMARY KEY,
  pdf_id              INT,
  student_id          INT NOT NULL,
  subject             VARCHAR(150) NOT NULL,
  difficulty          VARCHAR(20) NOT NULL DEFAULT 'Medium',
  question_types      JSON,
  question_count      INT DEFAULT 10,
  score               FLOAT,
  correct_count       INT,
  wrong_count         INT,
  time_taken_seconds  INT,
  submitted           BOOLEAN DEFAULT FALSE,
  created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
  submitted_at        DATETIME,
  FOREIGN KEY (pdf_id) REFERENCES pdf_uploads(pdf_id) ON DELETE SET NULL,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE quiz_questions (
  question_id     INT AUTO_INCREMENT PRIMARY KEY,
  quiz_id         INT NOT NULL,
  order_index     INT DEFAULT 0,
  question_type   VARCHAR(30) DEFAULT 'Multiple Choice',
  question_text   TEXT NOT NULL,
  choices         JSON,
  correct_answer  VARCHAR(500) NOT NULL,
  student_answer  VARCHAR(500),
  is_correct      BOOLEAN,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE
);

CREATE TABLE flashcards (
  flashcard_id  INT AUTO_INCREMENT PRIMARY KEY,
  pdf_id        INT,
  student_id    INT NOT NULL,
  subject       VARCHAR(150) NOT NULL,
  front         TEXT NOT NULL,
  back          TEXT NOT NULL,
  mastered      BOOLEAN DEFAULT FALSE,
  bookmarked    BOOLEAN DEFAULT FALSE,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (pdf_id) REFERENCES pdf_uploads(pdf_id) ON DELETE SET NULL,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE TABLE streaks (
  student_id          INT PRIMARY KEY,
  current_streak      INT DEFAULT 0,
  longest_streak      INT DEFAULT 0,
  last_quiz_date      DATE,
  average_score       FLOAT DEFAULT 0,
  quizzes_completed   INT DEFAULT 0,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);
