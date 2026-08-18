"""One-time migration: make student_number, course, and year_level nullable
in an existing SQLite database so that new registrations (which no longer
collect these fields) can be saved.

Run:
    python migrate_make_student_fields_nullable.py [path/to/quizify.db]

Default DB path: ./quizify.db
"""
import sqlite3
import sys

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "quizify.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Inspect the current students table schema.
row = cur.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='students'"
).fetchone()
if not row:
    print("No 'students' table found in", DB_PATH)
    sys.exit(1)

current_sql = row[0]
print("Current students schema:")
print(current_sql)
print("-" * 70)

if "student_number  VARCHAR(20) UNIQUE" in current_sql or "student_number VARCHAR(20) UNIQUE" in current_sql:
    print("Columns already nullable (or no NOT NULL constraints) — nothing to do.")
    conn.close()
    sys.exit(0)

print("Rebuilding students table with nullable student_number / course / year_level...")

# SQLite cannot ALTER COLUMN, so rebuild the table preserving existing data.
cur.executescript(
    """
    PRAGMA foreign_keys=OFF;
    BEGIN TRANSACTION;

    ALTER TABLE students RENAME TO students_old;

    CREATE TABLE students (
        student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        student_number  VARCHAR(20) UNIQUE,
        full_name       VARCHAR(120) NOT NULL,
        course          VARCHAR(10),
        year_level      VARCHAR(20) DEFAULT '1st Year',
        email           VARCHAR(150) NOT NULL UNIQUE,
        password_hash   VARCHAR(255) NOT NULL,
        is_admin        BOOLEAN DEFAULT FALSE,
        is_active       BOOLEAN DEFAULT TRUE,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO students (student_id, student_number, full_name, course, year_level, email, password_hash, is_admin, is_active, created_at)
        SELECT student_id, student_number, full_name, course, year_level, email, password_hash, is_admin, is_active, created_at FROM students_old;

    DROP TABLE students_old;

    COMMIT;
    PRAGMA foreign_keys=ON;
    """
)

# Verify
new_row = cur.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='students'"
).fetchone()
print("New students schema:")
print(new_row[0])
count = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
print("-" * 70)
print(f"Migration complete. {count} existing student rows preserved.")
conn.close()

