

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "notes.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the notes table if it doesn't already exist. Safe to call on every app start."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            description TEXT,
            uploader_email TEXT NOT NULL,
            uploader_name TEXT,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_note(title, subject, description, uploader_email, uploader_name,
             original_filename, stored_filename):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO notes (title, subject, description, uploader_email, uploader_name,
                            original_filename, stored_filename, upload_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            subject,
            description,
            uploader_email,
            uploader_name,
            original_filename,
            stored_filename,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    )
    conn.commit()
    conn.close()


def search_notes(query):
    """Search notes by title, subject, or description (case-insensitive substring match)."""
    conn = get_connection()
    like_query = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM notes
        WHERE title LIKE ? OR subject LIKE ? OR description LIKE ?
        ORDER BY id DESC
        """,
        (like_query, like_query, like_query),
    ).fetchall()
    conn.close()
    return rows


def get_all_notes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def get_notes_by_user(email):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes WHERE uploader_email = ? ORDER BY id DESC", (email,)
    ).fetchall()
    conn.close()
    return rows


def get_note_by_id(note_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return row


def delete_note(note_id, requester_email):
    """
    Delete a note's DB record AND its file on disk.
    Only succeeds if requester_email matches the uploader (ownership check),
    so a user can only delete their own notes.
    """
    note = get_note_by_id(note_id)
    if note is None:
        return False
    if note["uploader_email"] != requester_email:
        return False

    file_path = os.path.join(UPLOAD_DIR, note["stored_filename"])
    if os.path.exists(file_path):
        os.remove(file_path)

    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return True
