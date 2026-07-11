#Michael Winsted
#July 11, 2026
#SDC435L 3.3 project

import json
from cassandra.cluster import Cluster
#Create
#Notify when script is starting
print("Connecting to local Cassandra database...")


#Connect to a local Cassandra cluster
cluster = Cluster()
session = cluster.connect()

#DATABASE SETUP
query ="""Creates keyspace and repositories table."""
    session.execute("""
CREATE KEYSPACE IF NOT EXISTS github_license_db
    WITH replication = {
        'class':'SimpleStrategy',
        'replication_factor':1
    }
    """)

    session.set_keyspace("github_license_db")

    session.execute("""
    CREATE TABLE IF NOT EXISTS repositories (

        repo_name TEXT PRIMARY KEY,

        license TEXT
    )
    """)

    print("Database setup complete.")
#CHECK IF TABLE CONTAINS DATA
query ="""Returns True if table contains no data.
    Used to prevent duplicate imports."""

    rows = session.execute("""
    SELECT repo_name
    FROM repositories
    LIMIT 1
    """)

    return len(list(rows)) == 0
#LOAD JSON DATASET
#Import data from JSON file
for line in open('Licenses.json', 'r'):
    dataSet = json.loads(line)
# CREATE
#create table
def create_repository(session):

    print("\nCreate Repository")

    repo_name = input(
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
        repo_name,
        license_name
    ))

    print("Repository created successfully.")
# READ
def read_repository(session):

    print("\nRead Repository")

    repo_name = input(
        "Repository Name: "
    )

    rows = session.execute("""
    SELECT *
    FROM repositories
    WHERE repo_name=%s
    """,
    [repo_name])

    found = False

    for row in rows:

        found = True

        print("\nRepository Found")

        print(
            f"Repository : {row.repo_name}"
        )

        print(
            f"License    : {row.license}"
        )

    if not found:

        print("Repository not found.")
# UPDATE

def update_repository(session):

    print("\nUpdate Repository")

    repo_name = input(
        "Repository Name: "
    )

    new_license = input(
        "New License: "
    )

    session.execute("""
    UPDATE repositories
    SET license=%s
    WHERE repo_name=%s
    """,
    (
        new_license,
        repo_name
    ))

    print("Repository updated successfully.")
# DELETE

def delete_repository(session):

    print("\nDelete Repository")

    repo_name = input(
        "Repository Name: "
    )

    session.execute("""
    DELETE FROM repositories
    WHERE repo_name=%s
    """,
    [repo_name])

    print("Repository deleted successfully.")
# FEATURE 1
# LICENSE DISTRIBUTION
query =
    """
    Counts repositories by license.
    """

    rows = session.execute("""
    SELECT license
    FROM repositories
    """)

    licenses = []

    for row in rows:

        licenses.append(
            row.license
        )

    counts = Counter(
        licenses
    )

    print("\nTop License Distribution\n")

    for license_name, count in counts.most_common(10):

        print(f"{license_name:<20} {count}"        
# FEATURE 2
# SEARCH BY LICENSE
query ="""Displays repositories that use a specific license."""

    target_license = input(
        "\nEnter License Name: "
    )

    rows = session.execute("""
    SELECT *
    FROM repositories
    """)

    total = 0

    print("\nRepositories\n")

    for row in rows:

        if row.license == target_license:

            print(
                row.repo_name
            )

            total += 1

    print(
        f"\nTotal Found: {total}"
    )
    
# FEATURE 3
# LICENSE VISUALIZATION
query ="""Creates bar chart oftop 10 licenses."""

    rows = session.execute("""
    SELECT license
    FROM repositories
    """)

    licenses = []

    for row in rows:

        licenses.append(
            row.license
        )

    counts = Counter(
        licenses
    )

    top_ten = counts.most_common(10)

    labels = []

    values = []

    for item in top_ten:

        labels.append(item[0])

        values.append(item[1])

    plt.figure(figsize=(10, 6))

    plt.bar(
        labels,
        values
    )

    plt.title(
        "Top 10 GitHub Licenses"
    )

    plt.xlabel(
        "License Type"
    )

    plt.ylabel(
        "Number of Repositories"
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.show()
    
# MENU
def menu():

    session = connect_database()

    create_keyspace_and_table(
        session
    )

    session.set_keyspace(
        "github_license_db"
    )

    # *****************************
    # AUTO IMPORT DATASET
    # *****************************

    if is_table_empty(session):

        print(
            "\nLoading Licenses.json..."
        )

        load_json_data(
            session,
            "Licenses.json"
        )

        print(
            "Dataset loaded successfully."
        )

    else:

        print(
            "\nDataset already exists."
        )

    # **********************************
    # APPLICATION MENU
    # **********************************

    while True:

        print("\n")
        print("=" * 55)
        print("GitHub License Analytics System")
        print("=" * 55)

        print("1. Create Repository")
        print("2. Read Repository")
        print("3. Update Repository")
        print("4. Delete Repository")
        print("5. License Distribution")
        print("6. Search By License")
        print("7. Visualize Licenses")
        print("8. Exit")

        choice = input(
            "\nEnter Choice: "
        )

        if choice == "1":

            create_repository(
                session
            )

        elif choice == "2":

            read_repository(
                session
            )

        elif choice == "3":

            update_repository(
                session
            )

        elif choice == "4":

            delete_repository(
                session
            )

        elif choice == "5":

            license_distribution(
                session
            )

        elif choice == "6":

            search_by_license(
                session
            )

        elif choice == "7":

            visualize_licenses(
                session
            )

        elif choice == "8":

            print(
                "\nProgram terminated."
            )

            break

        else:

            print(
                "\nInvalid choice."
            )
# MAIN
if __name__ == "__menu__":

    menu()
