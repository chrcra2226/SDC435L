"""
sqlite_crud.py — SQLite Connection & CRUD Operations
======================================================
Handles the core SQLite functionality for the GitHub Archive application.

This module works with the GitHub commit dataset (Sample_Commits.json),
where each line is a JSON object describing a single Git commit pulled
from GitHub's public BigQuery dataset. Each commit record includes:
    commit      : the commit SHA (used as the unique primary key)
    author      : {"name": ..., "email": ...} — who wrote the commit
    committer   : {"name": ..., "email": ...} — who committed it
    repo_name   : the repository name as a plain string (e.g. "owner/repo")
    subject     : the first line of the commit message
    message     : the full commit message
    parent      : list of parent commit SHA(s)
    tree        : the tree SHA
    difference  : list of file changes — each entry has new_path, old_path,
                  new_mode, old_mode — unique to this dataset vs Commits.json

Unlike the other databases in this project, SQLite uses Python's built-in
sqlite3 module — no additional driver installation is required.

Database Schema:
  Table: commits
    sha          TEXT PRIMARY KEY
    repo_name    TEXT
    author_name  TEXT
    author_email TEXT
    subject      TEXT
    message      TEXT
    tree         TEXT
    files_changed INTEGER   ← derived from len(difference)

Responsibilities:
  - Database creation and schema setup
  - Data loading from JSON / JSONL files
  - Create, Read, Update, and Delete (CRUD) operations

Imported by menu.py and sqlite_features.py — do not run this file directly.
"""

import sqlite3
import json
import os


# ─────────────────────────────────────────
#  CONNECTION & SETUP
# ─────────────────────────────────────────

def connect_to_sqlite(db_path="data/databases/github_archive.db"):
    """
    Open (or create) an SQLite database file and return the connection.
    Creates the commits table if it does not already exist.

    SQLite databases are stored as a single file on disk — no server
    is required. The database file is created automatically if it does
    not exist at the given path.

    Args:
        db_path (str): Path to the SQLite database file.
                       Defaults to 'data/github_archive.db'.

    Returns:
        sqlite3.Connection: An active SQLite connection with the
                            commits table ready for use.
    """
    # Ensure the data directory exists before creating the db file
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # Allows column access by name

    # Enable WAL mode for better concurrent read performance
    conn.execute("PRAGMA journal_mode=WAL")

    # Create the commits table if it doesn't exist yet
    conn.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            sha           TEXT PRIMARY KEY,
            repo_name     TEXT,
            author_name   TEXT,
            author_email  TEXT,
            subject       TEXT,
            message       TEXT,
            tree          TEXT,
            files_changed INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    print(f"[OK] Connected to SQLite database at '{db_path}'.")
    return conn


# ─────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────

def load_github_data(filepath):
    """
    Load GitHub commit data from a JSONL file (one JSON object per line).

    Sample_Commits.json uses newline-delimited JSON — each line is one
    complete commit record. This is the same format as Commits.json but
    also includes a 'difference' field listing all file changes per commit.

    Args:
        filepath (str): Path to the commit data file (e.g. Sample_Commits.json).

    Returns:
        list: A list of commit dictionaries, or [] if file not found.
    """
    records = []

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return records

    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[WARN] Skipping malformed JSON on line {i}")

    print(f"[OK] Loaded {len(records)} commit records from {filepath}")
    return records


# ─────────────────────────────────────────
#  CRUD — CREATE
# ─────────────────────────────────────────

def create_commit(conn, commit):
    """
    Insert a single commit record into the SQLite commits table.
    Uses INSERT OR IGNORE to skip duplicates (keyed on SHA).

    Args:
        conn   (sqlite3.Connection): Active SQLite connection.
        commit (dict): A commit dictionary (from Sample_Commits.json).

    Returns:
        str: The commit SHA used as the primary key.
    """
    sha          = commit.get("commit", "unknown")
    repo_name    = commit.get("repo_name", "unknown")
    author_name  = commit.get("author", {}).get("name", "unknown")
    author_email = commit.get("author", {}).get("email", "")
    subject      = commit.get("subject", "").strip()
    message      = commit.get("message", "").strip()
    tree         = commit.get("tree", "")

    # Count the number of files changed using the difference field
    difference    = commit.get("difference", [])
    files_changed = len(difference) if isinstance(difference, list) else 0

    conn.execute("""
        INSERT OR IGNORE INTO commits
            (sha, repo_name, author_name, author_email,
             subject, message, tree, files_changed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (sha, repo_name, author_name, author_email,
          subject, message, tree, files_changed))
    conn.commit()

    return sha


def bulk_create_commits(conn, commits, batch_size=500):
    """
    Insert a list of commit records into SQLite using batch transactions.
    Batching reduces the number of disk writes and significantly improves
    insert performance compared to committing after each individual row.

    Args:
        conn       (sqlite3.Connection): Active SQLite connection.
        commits    (list):               List of commit dictionaries.
        batch_size (int):                Number of rows per transaction batch.

    Returns:
        int: Total number of commits inserted.
    """
    total = 0
    batch = []

    for i, commit in enumerate(commits, start=1):
        sha          = commit.get("commit", f"unknown_{i}")
        repo_name    = commit.get("repo_name", "unknown")
        author_name  = commit.get("author", {}).get("name", "unknown")
        author_email = commit.get("author", {}).get("email", "")
        subject      = commit.get("subject", "").strip()
        message      = commit.get("message", "").strip()
        tree         = commit.get("tree", "")
        difference   = commit.get("difference", [])
        files_changed = len(difference) if isinstance(difference, list) else 0

        batch.append((sha, repo_name, author_name, author_email,
                      subject, message, tree, files_changed))
        total += 1

        # Flush the batch when it reaches batch_size
        if i % batch_size == 0:
            conn.executemany("""
                INSERT OR IGNORE INTO commits
                    (sha, repo_name, author_name, author_email,
                     subject, message, tree, files_changed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            batch = []
            print(f"  ...inserted {i} commits so far")

    # Flush any remaining commits that didn't fill a full batch
    if batch:
        conn.executemany("""
            INSERT OR IGNORE INTO commits
                (sha, repo_name, author_name, author_email,
                 subject, message, tree, files_changed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()

    print(f"[OK] Stored {total} commits in SQLite.")
    return total


# ─────────────────────────────────────────
#  CRUD — READ
# ─────────────────────────────────────────

def read_commit(conn, sha):
    """
    Retrieve a single commit row from the SQLite commits table by SHA.

    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        sha  (str): The commit SHA to look up.

    Returns:
        dict or None: A dictionary of commit fields, or None if not found.
    """
    cursor = conn.execute("""
        SELECT sha, repo_name, author_name, author_email,
               subject, message, tree, files_changed
        FROM commits
        WHERE sha = ?
    """, (sha,))

    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def list_commits(conn, limit=20):
    """
    Return a list of stored commit SHAs and their subjects from SQLite.

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        limit (int): Maximum number of rows to return.

    Returns:
        list of tuples: [(sha, subject), ...]
    """
    cursor = conn.execute("""
        SELECT sha, subject FROM commits LIMIT ?
    """, (limit,))

    return [(row["sha"], row["subject"]) for row in cursor.fetchall()]


# ─────────────────────────────────────────
#  CRUD — UPDATE
# ─────────────────────────────────────────

def update_commit(conn, sha, field, value):
    """
    Update a single column on an existing commit row in SQLite.

    Only allows updating safe, non-primary-key columns to prevent
    accidental schema corruption from user input.

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        sha   (str): The commit SHA to update.
        field (str): The column name to change.
        value (str): The new value for that column.

    Returns:
        bool: True if the row was found and updated, False otherwise.
    """
    # Whitelist of columns that are safe to update
    allowed_fields = {"repo_name", "author_name", "author_email",
                      "subject", "message", "tree", "files_changed"}

    if field not in allowed_fields:
        print(f"[WARN] Field '{field}' is not updatable. "
              f"Allowed: {', '.join(sorted(allowed_fields))}")
        return False

    # Check the row exists before attempting the update
    existing = read_commit(conn, sha)
    if not existing:
        print(f"[WARN] Commit '{sha}' not found — cannot update.")
        return False

    # SQLite does not support parameterized column names, so we use
    # string formatting here — safe because field is whitelisted above.
    conn.execute(f"UPDATE commits SET {field} = ? WHERE sha = ?", (value, sha))
    conn.commit()

    print(f"[OK] Updated commit '{sha}': {field} = '{value}'.")
    return True


# ─────────────────────────────────────────
#  CRUD — DELETE
# ─────────────────────────────────────────

def delete_commit(conn, sha):
    """
    Delete a single commit row from the SQLite commits table by SHA.

    Args:
        conn (sqlite3.Connection): Active SQLite connection.
        sha  (str): The commit SHA to delete.

    Returns:
        bool: True if the row was deleted, False if it did not exist.
    """
    cursor = conn.execute("DELETE FROM commits WHERE sha = ?", (sha,))
    conn.commit()

    if cursor.rowcount > 0:
        print(f"[OK] Deleted commit '{sha}'.")
        return True

    print(f"[WARN] Commit '{sha}' not found — nothing deleted.")
    return False
