"""
neo4j_crud.py — Neo4j Connection & CRUD Operations
=====================================================
Handles the core Neo4j functionality for the GitHub Archive application.

This module works with the GitHub file dataset (Sample_Files.json), where
each line is a JSON object describing a single file tracked in a GitHub
repository. Each file record includes:
    repo_name      : the repository the file belongs to (e.g. "owner/repo")
    ref            : the git branch reference (e.g. "refs/heads/master")
    path           : the file path within the repository
    mode           : the file mode (e.g. "33188" for regular file)
    id             : the blob SHA identifying the file content
    symlink_target : symlink destination if the file is a symlink, else absent

Graph Data Model:
  (:File {id, path, mode, symlink_target})
      -[:BELONGS_TO]-> (:Repo {name})
      -[:ON_BRANCH]->  (:Branch {ref})

Responsibilities:
  - Connection management
  - Data loading from JSON / JSONL files
  - Create, Read, Update, and Delete (CRUD) operations on graph nodes

Imported by menu.py and neo4j_features.py — do not run this file directly.
"""

from neo4j import GraphDatabase
import json
import os


# ─────────────────────────────────────────
#  CONNECTION
# ─────────────────────────────────────────

def connect_to_neo4j(uri="bolt://localhost:7687", user="neo4j", password="Password1"):
    """
    Establish and return a Neo4j driver connection.
    Raises ConnectionError if Neo4j is unreachable.

    Args:
        uri      (str): Neo4j Bolt URI. Defaults to 'bolt://localhost:7687'.
        user     (str): Neo4j username. Defaults to 'neo4j'.
        password (str): Neo4j password. Defaults to 'Password1'.

    Returns:
        neo4j.GraphDatabase.driver: An active Neo4j driver instance.
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        # Verify the connection is alive with a lightweight check
        driver.verify_connectivity()
        print(f"[OK] Connected to Neo4j at {uri}")
        return driver
    except Exception as e:
        raise ConnectionError(f"[ERROR] Could not connect to Neo4j: {e}")


# ─────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────

def load_github_data(filepath):
    """
    Load GitHub file data from a JSONL file (one JSON object per line).

    Each line in Sample_Files.json is a JSON object describing a single
    file entry tracked in a GitHub repository.

    Args:
        filepath (str): Path to the file data file (e.g. Sample_Files.json).

    Returns:
        list: A list of file record dictionaries, or [] if file not found.
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

    print(f"[OK] Loaded {len(records)} file records from {filepath}")
    return records


# ─────────────────────────────────────────
#  CRUD — CREATE
# ─────────────────────────────────────────

def create_file_node(driver, record):
    """
    Store a single file record in Neo4j as a graph structure.

    Creates the following nodes and relationships (MERGE prevents duplicates):
      (:File)-[:BELONGS_TO]-> (:Repo)
      (:File)-[:ON_BRANCH]->  (:Branch)

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        record (dict): A file record dictionary (from Sample_Files.json).

    Returns:
        str: The file blob ID used as the unique identifier.
    """
    file_id  = record.get("id", "unknown")
    path     = record.get("path", "")
    mode     = record.get("mode", "")
    symlink  = record.get("symlink_target", "")
    repo     = record.get("repo_name", "unknown")
    ref      = record.get("ref", "unknown")

    with driver.session() as session:
        session.run("""
            MERGE (f:File   {id: $file_id})
              ON CREATE SET f.path    = $path,
                            f.mode    = $mode,
                            f.symlink = $symlink

            MERGE (r:Repo   {name: $repo})
            MERGE (b:Branch {ref:  $ref})

            MERGE (f)-[:BELONGS_TO]-> (r)
            MERGE (f)-[:ON_BRANCH]->  (b)
        """,
        file_id=file_id, path=path, mode=mode, symlink=symlink,
        repo=repo, ref=ref)

    return file_id


def bulk_create_files(driver, records, batch_size=500):
    """
    Store a list of file records in Neo4j using batched transactions.
    Each batch is committed as a single transaction to reduce round-trips.

    Args:
        driver     (neo4j.Driver): Active Neo4j driver.
        records    (list):         List of file record dictionaries.
        batch_size (int):          Number of records per transaction batch.

    Returns:
        int: Total number of file records stored.
    """
    total = 0

    def process_batch(tx, batch):
        """Write one batch of file records inside a single transaction."""
        tx.run("""
            UNWIND $rows AS row
            MERGE (f:File   {id: row.file_id})
              ON CREATE SET f.path    = row.path,
                            f.mode    = row.mode,
                            f.symlink = row.symlink

            MERGE (r:Repo   {name: row.repo})
            MERGE (b:Branch {ref:  row.ref})

            MERGE (f)-[:BELONGS_TO]-> (r)
            MERGE (f)-[:ON_BRANCH]->  (b)
        """, rows=batch)

    batch = []
    with driver.session() as session:
        for i, record in enumerate(records, start=1):
            batch.append({
                "file_id": record.get("id", f"unknown_{i}"),
                "path":    record.get("path", ""),
                "mode":    record.get("mode", ""),
                "symlink": record.get("symlink_target", ""),
                "repo":    record.get("repo_name", "unknown"),
                "ref":     record.get("ref", "unknown"),
            })
            total += 1

            # Flush the batch when it reaches batch_size
            if i % batch_size == 0:
                session.execute_write(process_batch, batch)
                batch = []
                print(f"  ...stored {i} file records so far")

        # Flush any remaining records that didn't fill a full batch
        if batch:
            session.execute_write(process_batch, batch)

    print(f"[OK] Stored {total} file records in Neo4j.")
    return total


# ─────────────────────────────────────────
#  CRUD — READ
# ─────────────────────────────────────────

def read_file_node(driver, file_id):
    """
    Retrieve a single File node and its connected Repo and Branch nodes
    from Neo4j by file blob ID.

    Args:
        driver  (neo4j.Driver): Active Neo4j driver.
        file_id (str):          The file blob ID to look up.

    Returns:
        dict or None: A dictionary of file details, or None if not found.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (f:File {id: $file_id})
            OPTIONAL MATCH (f)-[:BELONGS_TO]-> (r:Repo)
            OPTIONAL MATCH (f)-[:ON_BRANCH]->  (b:Branch)
            RETURN f.id      AS id,
                   f.path    AS path,
                   f.mode    AS mode,
                   f.symlink AS symlink,
                   r.name    AS repo,
                   b.ref     AS ref
        """, file_id=file_id)

        record = result.single()
        if record:
            return dict(record)
        return None


def list_files(driver, limit=20):
    """
    Return a list of stored file IDs from Neo4j.

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        limit  (int):          Maximum number of IDs to return.

    Returns:
        list: File blob ID strings.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (f:File)
            RETURN f.id AS id, f.path AS path
            LIMIT $limit
        """, limit=limit)

        return [(record["id"], record["path"]) for record in result]


# ─────────────────────────────────────────
#  CRUD — UPDATE
# ─────────────────────────────────────────

def update_file_node(driver, file_id, field, value):
    """
    Update a single property on an existing File node in Neo4j.

    Args:
        driver  (neo4j.Driver): Active Neo4j driver.
        file_id (str):          The file blob ID to update.
        field   (str):          The property name to change (e.g. 'path').
        value   (str):          The new value for that property.

    Returns:
        bool: True if the file was found and updated, False otherwise.
    """
    with driver.session() as session:
        # Check the file exists before attempting the update
        exists = session.run("""
            MATCH (f:File {id: $file_id}) RETURN count(f) AS cnt
        """, file_id=file_id).single()["cnt"]

        if not exists:
            print(f"[WARN] File '{file_id}' not found — cannot update.")
            return False

        # Use SET f += $props with a constructed map for dynamic property keys
        session.run("""
            MATCH (f:File {id: $file_id})
            SET f += $props
        """, file_id=file_id, props={field: value})

        print(f"[OK] Updated file '{file_id}': {field} = '{value}'.")
        return True


# ─────────────────────────────────────────
#  CRUD — DELETE
# ─────────────────────────────────────────

def delete_file_node(driver, file_id):
    """
    Delete a File node and all its relationships from Neo4j by blob ID.
    Uses DETACH DELETE to remove the node and its connected edges together.

    Args:
        driver  (neo4j.Driver): Active Neo4j driver.
        file_id (str):          The file blob ID to delete.

    Returns:
        bool: True if the node was deleted, False if it did not exist.
    """
    with driver.session() as session:
        # Count matches before deleting to report success/failure accurately
        count = session.run("""
            MATCH (f:File {id: $file_id}) RETURN count(f) AS cnt
        """, file_id=file_id).single()["cnt"]

        if not count:
            print(f"[WARN] File '{file_id}' not found — nothing deleted.")
            return False

        # DETACH DELETE removes the node AND all its relationships
        session.run("""
            MATCH (f:File {id: $file_id}) DETACH DELETE f
        """, file_id=file_id)

        print(f"[OK] Deleted file '{file_id}'.")
        return True
