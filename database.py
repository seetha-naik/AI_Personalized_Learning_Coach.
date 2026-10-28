import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "learning_coach.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                goal TEXT NOT NULL,
                level TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                daily_minutes INTEGER NOT NULL,
                plan TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                level TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_learning_plan(
    subject, goal, level, duration_days, daily_minutes, plan
):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO learning_plans (
                subject, goal, level, duration_days,
                daily_minutes, plan
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            subject, goal, level, duration_days,
            daily_minutes, plan
        ))
        return cursor.lastrowid


def get_all_learning_plans():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM learning_plans
            ORDER BY created_at DESC, id DESC
        """).fetchall()
        return [dict(row) for row in rows]


def save_quiz_result(subject, topic, level, score, total, percentage):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO quiz_results (
                subject, topic, level, score, total, percentage
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            subject, topic, level, score, total, percentage
        ))
        return cursor.lastrowid


def get_all_quiz_results():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM quiz_results
            ORDER BY created_at DESC, id DESC
        """).fetchall()
        return [dict(row) for row in rows]
