"""
redis_crud.py — Redis Connection & CRUD Operations
=====================================================
Handles the core Redis functionality for the GitHub Archive application.

This module works with the GitHub commit dataset (Commits.json), where
each line is a JSON object describing a single Git commit pulled from
GitHub's public BigQuery dataset. Each commit record includes:
    author     : {"name": ..., "email": ...}
    committer  : {"name": ..., "email": ...}
    commit     : the commit SHA (used as the unique Redis key)
    repo_name  : a LIST containing the repository name, e.g. ["owner/repo"]
    message    : the full commit message
    subject    : the first line of the commit message
    parent     : list of parent commit SHA(s)
    tree       : the tree SHA

Responsibilities:
  - Connection management
  - Data loading from JSON / JSONL files
  - Create, Read, Update, and Delete (CRUD) operations

Imported by menu.py and redis_features.py — do not run this file directly.
"""

import redis
import json
import os


# ─────────────────────────────────────────
#  CONNECTION
# ─────────────────────────────────────────

def connect_to_redis(host="localhost", port=6379, db=0):
    """
    Establish and return a Redis client connection.
    Raises ConnectionError if Redis is unreachable.

    Args:
        host (str): Redis server hostname. Defaults to 'localhost'.
        port (int): Redis server port. Defaults to 6379.
        db (int): Redis database index. Defaults to 0.

    Returns:
        redis.Redis: An active Redis client instance.
    """
    try:
        client = redis.Redis(host=host, port=port, db=db, decode_responses=True , protocol=2)
        client.ping()  # Verify the connection is alive
        print(f"[OK] Connected to Redis at {host}:{port}")
        return client
    except redis.ConnectionError as e:
        raise ConnectionError(f"[ERROR] Could not connect to Redis: {e}")


# ─────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────

def load_github_data(filepath):
    """
    Load GitHub commit data from a JSON or JSONL file.

    Supports:
      - .json  → A single JSON array of commit objects
      - .jsonl → One JSON commit object per line (this is the format
                 used by Commits.json in the GitHubArchive-Dataset)

    Args:
        filepath (str): Path to the commit data file (e.g. Commits.json).

    Returns:
        list: A list of commit dictionaries, or [] if file not found.
    """
    commits = []

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return commits

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Attempt to parse as a JSON array first
    if content.startswith("["):
        try:
            commits = json.loads(content)
            print(f"[OK] Loaded {len(commits)} commits from {filepath}")
            return commits
        except json.JSONDecodeError:
            pass

    # Fall back to JSONL (newline-delimited JSON) — this is the format
    # Commits.json actually uses: one JSON object per line.
    for i, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            commits.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[WARN] Skipping malformed JSON on line {i}")

    print(f"[OK] Loaded {len(commits)} commits from {filepath}")
    return commits


def get_repo_name(commit):
    """
    Safely extract the repository name from a commit record.

    In Commits.json, 'repo_name' is stored as a LIST (e.g. ["owner/repo"])
    rather than a plain string. This helper normalizes that so the rest
    of the application can treat repo_name as a simple string.

    Args:
        commit (dict): A single commit dictionary.

    Returns:
        str: The repository name, or "unknown" if not present.
    """
    repo_name = commit.get("repo_name", "unknown")
    if isinstance(repo_name, list):
        return repo_name[0] if repo_name else "unknown"
    return repo_name or "unknown"


# ─────────────────────────────────────────
#  CRUD — CREATE
# ─────────────────────────────────────────

def create_commit(client, commit):
    """
    Store a single commit in Redis as a serialized JSON string.
    Key format: commit:<commit_sha>

    Args:
        client (redis.Redis): Active Redis client.
        commit (dict): A commit dictionary (from Commits.json).

    Returns:
        str: The Redis key used to store the commit (e.g. 'commit:abcd123...').
    """
    commit_sha = commit.get("commit", "unknown")
    key = f"commit:{commit_sha}"
    client.set(key, json.dumps(commit))
    return key


def bulk_create_commits(client, commits, batch_size=500):
    """
    Store a list of commits in Redis using pipelining for efficiency.
    Pipelining batches multiple SET commands into a single network round-trip.

    Args:
        client (redis.Redis): Active Redis client.
        commits (list): List of commit dictionaries.
        batch_size (int): Number of SET commands to batch before flushing.

    Returns:
        int: Total number of commits stored.
    """
    total = 0
    pipe = client.pipeline()

    for i, commit in enumerate(commits, start=1):
        commit_sha = commit.get("commit", f"unknown_{i}")
        pipe.set(f"commit:{commit_sha}", json.dumps(commit))
        total += 1

        if i % batch_size == 0:
            pipe.execute()
            pipe = client.pipeline()
            print(f"  ...stored {i} commits so far")

    pipe.execute()  # Flush any remaining commands
    print(f"[OK] Stored {total} commits in Redis.")
    return total


# ─────────────────────────────────────────
#  CRUD — READ
# ─────────────────────────────────────────

def read_commit(client, commit_sha):
    """
    Retrieve a single commit from Redis by its SHA.

    Args:
        client (redis.Redis): Active Redis client.
        commit_sha (str): The commit SHA (without the 'commit:' prefix).

    Returns:
        dict or None: The commit dictionary, or None if not found.
    """
    data = client.get(f"commit:{commit_sha}")
    if data:
        return json.loads(data)
    return None


def list_all_commit_ids(client, limit=20):
    """
    Scan Redis for stored commit keys and return a list of commit SHAs.

    Args:
        client (redis.Redis): Active Redis client.
        limit (int): Maximum number of SHAs to return.

    Returns:
        list: Commit SHA strings (without the 'commit:' prefix).
    """
    ids = []
    for key in client.scan_iter("commit:*", count=100):
        ids.append(key.replace("commit:", ""))
        if len(ids) >= limit:
            break
    return ids


# ─────────────────────────────────────────
#  CRUD — UPDATE
# ─────────────────────────────────────────

def update_commit(client, commit_sha, updates):
    """
    Merge updated fields into an existing commit stored in Redis.
    Reads the current value, applies updates, then writes it back.

    Args:
        client (redis.Redis): Active Redis client.
        commit_sha (str): The commit SHA to update.
        updates (dict): Fields to add or overwrite on the stored commit.

    Returns:
        bool: True if updated successfully, False if commit was not found.
    """
    existing = read_commit(client, commit_sha)
    if existing is None:
        print(f"[WARN] Commit '{commit_sha}' not found — cannot update.")
        return False

    existing.update(updates)
    client.set(f"commit:{commit_sha}", json.dumps(existing))
    print(f"[OK] Updated commit '{commit_sha}'.")
    return True


# ─────────────────────────────────────────
#  CRUD — DELETE
# ─────────────────────────────────────────

def delete_commit(client, commit_sha):
    """
    Delete a commit from Redis by its SHA.

    Args:
        client (redis.Redis): Active Redis client.
        commit_sha (str): The commit SHA to delete.

    Returns:
        bool: True if the key was deleted, False if it did not exist.
    """
    result = client.delete(f"commit:{commit_sha}")
    if result:
        print(f"[OK] Deleted commit '{commit_sha}'.")
        return True
    print(f"[WARN] Commit '{commit_sha}' not found — nothing deleted.")
    return False
