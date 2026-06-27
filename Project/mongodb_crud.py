"""
mongodb_crud.py
=============================
CRUD operations for MongoDB 
Dataset: sample_repos.json
Schema: repo_name, watch_count
"""

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

    try:
        client = MongoClient(uri)
        client.admin.command("ping")

        print("[OK] Connected to MongoDB")

        db = client[database]
        return db[collection]

    except ConnectionFailure:
        print("[ERROR] MongoDB connection failed")
        return None


# -----------------------------------------------------
# LOAD DATA (sample_repos.json)
# -----------------------------------------------------

import json

def load_github_data(filepath="sample_Repos.json"):

    data = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)

                    # Validate structure
                    if "repo_name" not in item or "watch_count" not in item:
                        raise ValueError("JSON must contain repo_name and watch_count")

                    # convert watch_count to int (IMPORTANT)
                    item["watch_count"] = int(item["watch_count"])

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

    if not collection or not data:
        return

    collection.delete_many({})  # reset collection
    collection.insert_many(data)

    print(f"[OK] Inserted {len(data)} repositories")


# -----------------------------------------------------
# READ
# -----------------------------------------------------

def read_repo(collection, repo_name):

    return collection.find_one(
        {"repo_name": repo_name},
        {"_id": 0}
    )


# -----------------------------------------------------
# UPDATE (watch_count safe increment or set)
# -----------------------------------------------------

def update_repo(collection, repo_name, updates):

    result = collection.update_one(
        {"repo_name": repo_name},
        {"$set": updates}
    )

    if result.modified_count:
        print("[OK] Updated")
    else:
        print("[WARN] Repo not found")


# -----------------------------------------------------
# DELETE
# -----------------------------------------------------

def delete_repo(collection, repo_name):

    result = collection.delete_one({"repo_name": repo_name})

    if result.deleted_count:
        print("[OK] Deleted")
    else:
        print("[WARN] Repo not found")


# -----------------------------------------------------
# LIST ALL REPOS
# -----------------------------------------------------

def list_all_repos(collection, limit=20):

    cursor = collection.find({}, {"repo_name": 1, "watch_count": 1, "_id": 0}).limit(limit)

    return list(cursor)
