"""
mongodb_crud.py
=============================
CRUD operations for MongoDB
Dataset: sample_repos.json
Schema: repo_name, watch_count
"""

# Import required libraries
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# -----------------------------------------------------
# CONNECTION
# -----------------------------------------------------

def connect_to_mongodb(
    uri="mongodb://localhost:27017/",
    database="GitHubArchive_Mongo",
    collection="Repos"
):
    """
    Connect to MongoDB and return the selected collection.
    """

    try:
        # Create MongoDB client
        client = MongoClient(uri)

        # Verify that the server is running
        client.admin.command("ping")

        print("[OK] Connected to MongoDB")

        # Select database
        db = client[database]

        # Return the requested collection
        return db[collection]

    except ConnectionFailure:
        print("[ERROR] MongoDB connection failed")
        return None


# -----------------------------------------------------
# LOAD DATA (sample_repos.json)
# -----------------------------------------------------

def load_github_data(filepath="Sample_Repos.json"):
    """
    Load repository data from a JSON file.

    Each line in the file should contain one JSON object with:
    - repo_name
    - watch_count
    """

    # Store all repositories here
    data = []

    try:
        # Open the JSON file
        with open(filepath, "r", encoding="utf-8") as f:

            # Read file line by line
            for line in f:

                # Remove extra whitespace
                line = line.strip()

                # Ignore blank lines
                if line:

                    # Convert JSON text into a Python dictionary
                    item = json.loads(line)

                    # Ensure required fields exist
                    if "repo_name" not in item or "watch_count" not in item:
                        raise ValueError(
                            "JSON must contain repo_name and watch_count"
                        )

                    # Convert watch_count from string to integer
                    item["watch_count"] = int(item["watch_count"])

                    # Add repository to the list
                    data.append(item)

        print(f"[OK] Loaded {len(data)} repositories")

        return data

    except Exception as e:
        print("[ERROR]", e)
        return []


# -----------------------------------------------------
# CREATE (BULK INSERT)
# -----------------------------------------------------

def bulk_create_repos(collection, data):
    """
    Insert all repositories into MongoDB.
    Existing documents are removed before inserting.
    """

    # Stop if collection or data is invalid
    if collection is None or not data:
        return

    try:
        # Remove any existing documents
        collection.delete_many({})

        # Insert all repositories at once
        collection.insert_many(data)

        print(f"[OK] Inserted {len(data)} repositories")

    except Exception as e:
        print("[ERROR] Insert failed:", e)


# -----------------------------------------------------
# READ
# -----------------------------------------------------

def read_repo(collection, repo_name):
    """
    Find and return one repository by its name.
    """

    return collection.find_one(
        {"repo_name": repo_name},   # Search condition
        {"_id": 0}                  # Exclude MongoDB ID field
    )


# -----------------------------------------------------
# UPDATE
# -----------------------------------------------------

def update_repo(collection, repo_name, updates):
    """
    Update fields of a repository.
    Example:
        updates = {"watch_count": 5000}
    """

    # Update matching repository
    result = collection.update_one(
        {"repo_name": repo_name},
        {"$set": updates}
    )

    # Check whether the update succeeded
    if result.modified_count:
        print("[OK] Updated")
    else:
        print("[WARN] Repo not found")


# -----------------------------------------------------
# DELETE
# -----------------------------------------------------

def delete_repo(collection, repo_name):
    """
    Delete a repository by its name.
    """

    # Delete matching repository
    result = collection.delete_one({"repo_name": repo_name})

    # Check whether deletion occurred
    if result.deleted_count:
        print("[OK] Deleted")
    else:
        print("[WARN] Repo not found")


# -----------------------------------------------------
# LIST ALL REPOSITORIES
# -----------------------------------------------------

def list_all_repos(collection, limit=20):
    """
    Return a list of repositories.

    Parameters:
        limit : Maximum number of repositories to return.
    """

    # Retrieve repository name and watch count only
    cursor = collection.find(
        {},
        {
            "repo_name": 1,
            "watch_count": 1,
            "_id": 0
        }
    ).limit(limit)

    # Convert cursor into a Python list
    return list(cursor)
