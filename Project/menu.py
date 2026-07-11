"""
menu.py — Interactive Menu
============================
Entry point for the GitHub Archive multi-database application.
Presents a main menu to select a database, then a submenu for
the chosen database's CRUD and feature options.

This application works with the GitHub commit dataset (Commits.json),
where each record represents a single Git commit (author, committer,
repo_name, commit SHA, message/subject, parent SHA(s), tree SHA).

Structure:
  Main Menu  →  1. Redis   (fully implemented)
                2. MongoDB     (fully implemented)
                3. Cassandra   (fully implemented)
                4. Neo4j       (coming soon)
                5. SQLite      (coming soon)
                0. Exit

  Redis Submenu → CRUD operations + 3 analytical features
    CRUD calls    → redis_crud.py
    Feature calls → redis_features.py

Usage:
  python menu.py
"""

import json
import redis_crud
import redis_features
import mongodb_crud
import mongodb_features
from cassandra.cluster import Cluster


# ─────────────────────────────────────────
#  REDIS DISPLAY HELPERS
# ─────────────────────────────────────────

def display_top_repos(client, top_n=10):
    """
    Print the most active repositories ranking to the console.
    Calls redis_features.get_top_repos() to fetch data.

    Args:
        client (redis.Redis): Active Redis client.
        top_n (int): Number of repositories to display.
    """
    repos = redis_features.get_top_repos(client, top_n)

    print(f"\n{'─'*50}")
    print(f"  Top {top_n} Most Active Repositories (by commit count)")
    print(f"{'─'*50}")

    if not repos:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*50}\n")
        return

    for rank, (repo, count) in enumerate(repos, start=1):
        bar = "█" * min(count, 30)  # ASCII bar capped at 30 chars wide
        print(f"  {rank:>2}. {repo:<35} {count:>5} commits  {bar}")

    print(f"{'─'*50}\n")


def display_commit_keyword_analysis(client):
    """
    Print commit message keyword frequency analysis to the console.
    Calls redis_features.get_commit_keyword_frequencies() to fetch data.

    Args:
        client (redis.Redis): Active Redis client.
    """
    frequencies = redis_features.get_commit_keyword_frequencies(client, top_n=15)

    print(f"\n{'─'*55}")
    print("  Commit Message Keyword Frequency Analysis")
    print("  (most common first word of commit subjects)")
    print(f"{'─'*55}")

    if not frequencies:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*55}\n")
        return

    total = sum(count for _, count in frequencies)

    for keyword, count in frequencies:
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)  # Scale to percentage
        print(f"  {keyword:<20} {count:>6} ({pct:5.1f}%)  {bar}")

    print(f"{'─'*55}")
    print(f"  Total (top 15 keywords): {total}")
    print(f"{'─'*55}\n")


def display_author_contribution_history(client, author_name):
    """
    Print a single author's contribution history to the console.
    Calls redis_features.get_author_contribution_history() to fetch data.

    Args:
        client (redis.Redis): Active Redis client.
        author_name (str): The commit author's name to look up.
    """
    history = redis_features.get_author_contribution_history(client, author_name)

    print(f"\n{'─'*50}")
    print(f"  Contribution History: {history['author_name']}")
    print(f"{'─'*50}")
    print(f"  Total commits recorded: {history['total_commits']}")

    commits = history["recent_commits"]
    if not commits:
        print("  No commits found for this author.")
        print(f"{'─'*50}\n")
        return

    print(f"  Most recent {len(commits)} commit(s):\n")
    for commit in commits:
        repo = redis_crud.get_repo_name(commit)
        subject = commit.get("subject", "N/A")
        sha = commit.get("commit", "N/A")
        print(f"    Repo: {repo}")
        print(f"     SHA: {sha[:12]}...  |  Subject: {subject}\n")

    print(f"{'─'*50}\n")


def display_top_contributors(client, top_n=10):
    """
    Print the top contributors leaderboard to the console.
    Calls redis_features.get_top_contributors() to fetch data.

    Args:
        client (redis.Redis): Active Redis client.
        top_n (int): Number of contributors to display.
    """
    contributors = redis_features.get_top_contributors(client, top_n)

    print(f"\n{'─'*50}")
    print(f"  Top {top_n} Contributors (by commit count)")
    print(f"{'─'*50}")

    if not contributors:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*50}\n")
        return

    for rank, (author, count) in enumerate(contributors, start=1):
        print(f"  {rank:>2}. {author:<35} {count:>5} commits")

    print(f"{'─'*50}\n")


# ─────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────

def print_main_menu():
    """Display the top-level database selection menu."""
    print("\n" + "=" * 50)
    print("   GitHub Archive — Database Explorer")
    print("=" * 50)
    print("  Select a database to work with:\n")
    print("    1. Redis")
    print("    2. MongoDB")
    print("    3. Cassandra")
    print("    4. Neo4j")
    print("    5. SQLite")
    print()
    print("    0. Exit")
    print("=" * 50)


# ─────────────────────────────────────────
#  REDIS SUBMENU
# ─────────────────────────────────────────

def print_redis_menu():
    """Display the Redis-specific CRUD and features submenu."""
    print("\n" + "=" * 50)
    print("   Redis — GitHub Commit Data")
    print("=" * 50)
    print("  CRUD Operations:")
    print("    1. Load & store all commits from file")
    print("    2. Read a specific commit by SHA")
    print("    3. Update a commit field")
    print("    4. Delete a commit by SHA")
    print("    5. List stored commit SHAs")
    print()
    print("  Features:")
    print("    6. [Feature 1] Most active repositories")
    print("    7. [Feature 2] Commit keyword frequency analysis")
    print("    8. [Feature 3] Top contributors leaderboard")
    print("    9. [Feature 3] Author contribution history")
    print()
    print("    0. Back to main menu")
    print("=" * 50)


def run_redis_menu(data_filepath="data/Commits.json"):
    """
    Connect to Redis and run the Redis submenu loop.
    Returns to the main menu when the user enters 0.

    Args:
        data_filepath (str): Default path to the commit data file
                              (Commits.json from GitHubArchive-Dataset.zip).
    """
    # Establish Redis connection via the CRUD module
    client = redis_crud.connect_to_redis()

    while True:
        print_redis_menu()
        choice = input("  Enter choice: ").strip()

        # ── CRUD ──────────────────────────────────────────────────────────

        if choice == "1":
            # Load data from file, store it, then build all feature indexes
            path = input(f"  File path [{data_filepath}]: ").strip() or data_filepath
            commits = redis_crud.load_github_data(path)
            if commits:
                redis_crud.bulk_create_commits(client, commits)
                redis_features.build_repo_activity_index(client, commits)
                redis_features.build_commit_keyword_index(client, commits)
                redis_features.build_author_contribution_index(client, commits)
                print("[OK] All indexes built successfully.")

        elif choice == "2":
            # Read a single commit by its SHA
            commit_sha = input("  Enter commit SHA: ").strip()
            commit = redis_crud.read_commit(client, commit_sha)
            if commit:
                print(f"\n  Commit data:\n{json.dumps(commit, indent=4)}")
            else:
                print(f"  [WARN] Commit '{commit_sha}' not found.")

        elif choice == "3":
            # Update a field on an existing commit
            commit_sha = input("  Enter commit SHA to update: ").strip()
            field      = input("  Field name to update: ").strip()
            value      = input("  New value: ").strip()
            redis_crud.update_commit(client, commit_sha, {field: value})

        elif choice == "4":
            # Delete a commit by its SHA
            commit_sha = input("  Enter commit SHA to delete: ").strip()
            redis_crud.delete_commit(client, commit_sha)

        elif choice == "5":
            # List stored commit SHAs
            limit = input("  How many SHAs to show? [20]: ").strip()
            limit = int(limit) if limit.isdigit() else 20
            ids = redis_crud.list_all_commit_ids(client, limit=limit)
            print(f"\n  Stored commit SHAs (showing up to {limit}):")
            for sha in ids:
                print(f"    {sha}")
            if not ids:
                print("  No commits stored yet.")

        # ── FEATURES ──────────────────────────────────────────────────────

        elif choice == "6":
            # Feature 1: Most active repositories
            top_n = input("  How many top repos to show? [10]: ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10
            display_top_repos(client, top_n)

        elif choice == "7":
            # Feature 2: Commit message keyword frequency analysis
            display_commit_keyword_analysis(client)

        elif choice == "8":
            # Feature 3: Top contributors leaderboard
            top_n = input("  How many top contributors to show? [10]: ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10
            display_top_contributors(client, top_n)

        elif choice == "9":
            # Feature 3: Individual author contribution history
            author_name = input("  Enter commit author name: ").strip()
            display_author_contribution_history(client, author_name)

        elif choice == "0":
            # Return to the main menu
            print("\n  Returning to main menu...")
            break

        else:
            print("  [WARN] Invalid choice. Please try again.")
# =====================================================
# MONGODB MENU 
# =====================================================
def run_mongodb_menu(data_filepath="data/Sample_Repos.json"):

    collection = mongodb_crud.connect_to_mongodb()

    if collection is None:
        print("Cannot connect to MongoDB.")
        return

    while True:

        print("\n--- MONGODB MENU ---")
        print("1 Load")
        print("2 Read")
        print("3 Update")
        print("4 Delete")
        print("5 List Repos")
        print("6 Repo Name Length Analysis")
        print("7 Top Watch Count")
        print("8 Watch Statistics")
        print("0 Back")

        choice = input("Choice: ")

        # -------------------------------------------------
        # LOAD JSON → MONGODB
        # -------------------------------------------------
        if choice == "1":

            data = mongodb_crud.load_github_data(data_filepath)

            if data:
                mongodb_crud.bulk_create_repos(collection, data)
                print("[OK] MongoDB loaded from Sample_Repos.json")
            else:
                print("[ERROR] No data loaded.")

        # -------------------------------------------------
        # READ ONE REPO
        # -------------------------------------------------
        elif choice == "2":

            name = input("Repo name: ")
            print(mongodb_crud.read_repo(collection, name))

        # -------------------------------------------------
        # UPDATE REPO
        # -------------------------------------------------
        elif choice == "3":

            name = input("Repo name: ")
            field = input("Field (repo_name/watch_count): ")
            value = input("Value: ")

            # convert watch_count to int if needed
            if field == "watch_count":
                value = int(value)

            mongodb_crud.update_repo(collection, name, {field: value})

        # -------------------------------------------------
        # DELETE REPO
        # -------------------------------------------------
        elif choice == "4":

            name = input("Repo name: ")
            mongodb_crud.delete_repo(collection, name)

        # -------------------------------------------------
        # LIST ALL REPOS
        # -------------------------------------------------
        elif choice == "5":

            print(mongodb_crud.list_all_repos(collection))

        # -------------------------------------------------
        # FEATURE 1: NAME LENGTH ANALYSIS
        # -------------------------------------------------
        elif choice == "6":

            mongodb_features.display_repo_name_lengths(collection)

        # -------------------------------------------------
        # FEATURE 2: TOP WATCHED REPOS
        # -------------------------------------------------
        elif choice == "7":

            mongodb_features.display_top_repositories(collection)

        # -------------------------------------------------
        # FEATURE 3: WATCH STATISTICS
        # -------------------------------------------------
        elif choice == "8":

            mongodb_features.display_watch_statistics(collection)

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------
        elif choice == "0":
            break

        else:
            print("[WARN] Invalid choice. Try again.")
def run_app():
    """
    Run the top-level database selection menu.
    Routes to the appropriate database submenu based on user choice.
    Placeholder databases print a coming-soon message and return here.
    """
    while True:
        print_main_menu()
        choice = input("  Enter choice: ").strip()

        if choice == "1":
            # Redis — fully implemented
            run_redis_menu()
        elif choice == "2":
            #Mongodb - fully implemented
            run_mongodb_menu()
        elif choice == "3":
            # cassandra — fully implemented
            run_cassandra_menu()
        elif choice in ( "4", "5"):
            # Placeholder databases — not yet implemented
            db_names = { "4": "Neo4j", "5": "SQLite"}
            print(f"\n  [Option under construction] {db_names[choice]} coming soon.")
            print("  Returning to main menu...")

        elif choice == "0":
            print("\n  Goodbye!\n")
            break

        else:
            print("  [WARN] Invalid choice. Please try again.")
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

          
# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    run_app()
