import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def initialize_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS patients (patientId TEXT PRIMARY KEY, name TEXT, dob TEXT, gender TEXT, payerId TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS providers (providerId TEXT PRIMARY KEY, npi TEXT, name TEXT, specialty TEXT, phone TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS payers (payerId TEXT PRIMARY KEY, name TEXT, planName TEXT, active INTEGER)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS drugs (drugNdc TEXT PRIMARY KEY, name TEXT, strength TEXT, form TEXT, copay REAL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS claims (claimId INTEGER PRIMARY KEY AUTOINCREMENT, patientId TEXT, providerId TEXT, drugNdc TEXT, amount REAL, status TEXT, submittedAt TEXT)"
        )
        conn.commit()
        print(f"Initialized SQLite database at {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_db()
