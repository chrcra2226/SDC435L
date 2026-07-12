# Michael Winstead
# July 11, 2026
# SDC435L 3.3 Project

import json
from cassandra.cluster import Cluster
from collections import Counter
import matplotlib.pyplot as plt


# =====================================================
# CONNECT TO CASSANDRA
# =====================================================

print("Connecting to local Cassandra database...")

cluster = Cluster()
session = cluster.connect()

# =====================================================
# DATABASE SETUP
# =====================================================

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

# =====================================================
# CRUD FUNCTIONS
# =====================================================

def create_repository():

    print("\n--- Create Repository ---")

    repo_name = input("Repository Name: ")
    license_name = input("License: ")

    session.execute("""
    INSERT INTO repositories (repo_name, license)
    VALUES (%s, %s)
    """, (repo_name, license_name))

    print("Repository created successfully.")


def read_repository():

    print("\n--- Read Repository ---")

    repo_name = input("Repository Name: ")

    rows = session.execute("""
    SELECT *
    FROM repositories
    WHERE repo_name=%s
    """, [repo_name])

    found = False

    for row in rows:
        found = True

        print("\nRepository Found")
        print(f"Repository : {row.repo_name}")
        print(f"License    : {row.license}")

    if not found:
        print("Repository not found.")


def update_repository():

    print("\n--- Update Repository ---")

    repo_name = input("Repository Name: ")
    new_license = input("New License: ")

    session.execute("""
    UPDATE repositories
    SET license=%s
    WHERE repo_name=%s
    """, (new_license, repo_name))

    print("Repository updated successfully.")


def delete_repository():

    print("\n--- Delete Repository ---")

    repo_name = input("Repository Name: ")

    session.execute("""
    DELETE FROM repositories
    WHERE repo_name=%s
    """, [repo_name])

    print("Repository deleted successfully.")


# =====================================================
# ANALYTICS FUNCTIONS
# =====================================================

def license_distribution():

    rows = session.execute("""
    SELECT license
    FROM repositories
    """)

    licenses = [row.license for row in rows]

    counts = Counter(licenses)

    print("\nTop License Distribution\n")

    for license_name, count in counts.most_common(10):
        print(f"{license_name:<20} {count}")

#FUNCTION 1
#=======================================
def search_by_license():

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

            print(row.repo_name)
            total += 1

    print(f"\nTotal Found: {total}")

#FUNCTION 2
#================================================
def visualize_licenses():

    rows = session.execute("""
    SELECT license
    FROM repositories
    """)

    licenses = [row.license for row in rows]

    counts = Counter(licenses)

    top_ten = counts.most_common(10)

    labels = [item[0] for item in top_ten]
    values = [item[1] for item in top_ten]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)

    plt.title("Top 10 GitHub Licenses")
    plt.xlabel("License Type")
    plt.ylabel("Number of Repositories")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()

#fUNTION 3
#===================================================
def record_count():

    rows = session.execute("""
    SELECT repo_name
    FROM repositories
    """)

    count = len(list(rows))

    print(f"\nTotal Records: {count}")


# =====================================================
# MENU
# =====================================================

def menu():

    while True:

        print("\n" + "=" * 60)
        print("      GitHub License Analytics System")
        print("=" * 60)

        print("\nCRUD OPERATIONS")
        print("  1. Create Repository")
        print("  2. Read Repository")
        print("  3. Update Repository")
        print("  4. Delete Repository")

        print("\nANALYTICS")
        print("  5. License Distribution")
        print("  6. Search by License")
        print("  7. Visualize Top Licenses")

        print("\nSYSTEM")
        print("  8. Show Record Count")
        print("  9. Exit")

        print("-" * 60)

        choice = input("Select an option (1-9): ")

        if choice == "1":
            create_repository()

        elif choice == "2":
            read_repository()

        elif choice == "3":
            update_repository()

        elif choice == "4":
            delete_repository()

        elif choice == "5":
            license_distribution()

        elif choice == "6":
            search_by_license()

        elif choice == "7":
            visualize_licenses()

        elif choice == "8":
            record_count()

        elif choice == "9":

            print("\nThank you for using")
            print("GitHub License Analytics System")
            print("Goodbye!")

            break

        else:

            print("\nInvalid selection. Try again.")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    menu()
