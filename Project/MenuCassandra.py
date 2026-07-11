# Michael Winstead
# July 11, 2026
# SDC435L 3.3 Project

import json
import redis
from pymongo import MongoClient
from cassandra.cluster import Cluster



# DATABASE CONNECTIONS
def connect_cassandra():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS github_license_db
    WITH replication = {
        'class':'SimpleStrategy',
        'replication_factor':1
    }
    """)

    session.set_keyspace("github_license_db")

    session.execute("""
    CREATE TABLE IF NOT EXISTS repositories(
        repo_name TEXT PRIMARY KEY,
        license TEXT
    )
    """)

    return session


def connect_mongodb():

    client = MongoClient(
        "mongodb://localhost:27017/"
    )

    db = client["github_license_db"]

    return db


def connect_redis():

    return redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )



# LOAD JSON INTO ALL DATABASES
def load_json_all(
        cassandra_session,
        mongodb,
        redis_db,
        filename
):

    with open(filename, "r") as file:

        for line in file:

            data = json.loads(line)

            repo = data["repo_name"]
            license_name = data["license"]

            # Cassandra

            cassandra_session.execute("""
            INSERT INTO repositories(
                repo_name,
                license
            )
            VALUES (%s,%s)
            """,
            (
                repo,
                license_name
            ))

            # MongoDB

            mongodb.repositories.insert_one(
                {
                    "repo_name": repo,
                    "license": license_name
                }
            )

            # Redis

            redis_db.hset(
                f"repo:{repo}",
                mapping={
                    "license": license_name
                }
            )

    print(
        "Data loaded into all databases."
    )
    
# CASSANDRA CRUD
def cassandra_create(session):

    repo = input(
        "Repository Name: "
    )

    license_name = input(
        "License: "
    )

    session.execute("""
    INSERT INTO repositories(
        repo_name,
        license
    )
    VALUES (%s,%s)
    """,
    (
        repo,
        license_name
    ))

    print("Created.")


def cassandra_read(session):

    repo = input(
        "Repository Name: "
    )

    rows = session.execute("""
    SELECT *
    FROM repositories
    WHERE repo_name=%s
    """,
    [repo])

    for row in rows:

        print(
            row.repo_name,
            row.license
        )

# MONGODB CRUD
def mongo_create(db):

    repo = input(
        "Repository Name: "
    )

    license_name = input(
        "License: "
    )

    db.repositories.insert_one(
        {
            "repo_name": repo,
            "license": license_name
        }
    )

    print("Created.")


def mongo_read(db):

    repo = input(
        "Repository Name: "
    )

    result = db.repositories.find_one(
        {
            "repo_name": repo
        }
    )

    print(result)

# REDIS CRUD
def redis_create(r):

    repo = input(
        "Repository Name: "
    )

    license_name = input(
        "License: "
    )

    r.hset(
        f"repo:{repo}",
        mapping={
            "license": license_name
        }
    )

    print("Created.")


def redis_read(r):

    repo = input(
        "Repository Name: "
    )

    result = r.hgetall(
        f"repo:{repo}"
    )

    print(result)



# MENUS
def cassandra_menu(session):

    while True:

        print("\nCASSANDRA MENU")
        print("1. Create")
        print("2. Read")
        print("3. Back")

        choice = input("Choice: ")

        if choice == "1":
            cassandra_create(session)

        elif choice == "2":
            cassandra_read(session)

        elif choice == "3":
            break


def mongodb_menu(db):

    while True:

        print("\nMONGODB MENU")
        print("1. Create")
        print("2. Read")
        print("3. Back")

        choice = input("Choice: ")

        if choice == "1":
            mongo_create(db)

        elif choice == "2":
            mongo_read(db)

        elif choice == "3":
            break


def redis_menu(r):

    while True:

        print("\nREDIS MENU")
        print("1. Create")
        print("2. Read")
        print("3. Back")

        choice = input("Choice: ")

        if choice == "1":
            redis_create(r)

        elif choice == "2":
            redis_read(r)

        elif choice == "3":
            break

# MAIN
def main():

    cassandra_session = connect_cassandra()

    mongodb = connect_mongodb()

    redis_db = connect_redis()

    load_json_all(
        cassandra_session,
        mongodb,
        redis_db,
        "Licenses.json"
    )

    while True:

        print("\n")
        print("=" * 50)
        print("GitHub License Analytics System")
        print("=" * 50)

        print("1. Cassandra")
        print("2. MongoDB")
        print("3. Redis")
        print("4. Exit")

        choice = input(
            "Choice: "
        )

        if choice == "1":

            cassandra_menu(
                cassandra_session
            )

        elif choice == "2":

            mongodb_menu(
                mongodb
            )

        elif choice == "3":

            redis_menu(
                redis_db
            )

        elif choice == "4":

            print("Goodbye")
            break


if __name__ == "__main__":
    main()
