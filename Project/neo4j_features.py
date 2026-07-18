"""
neo4j_features.py — Analytical Features
==========================================
Implements the three key analytical features for the GitHub file
dataset application using Neo4j graph traversal and aggregation:

  - Feature 1: Top Repositories by File Count
               Traverses (:File)-[:BELONGS_TO]->(:Repo) relationships
               to rank repositories by how many tracked files they contain.

  - Feature 2: Shared File Detection Across Repositories
               Finds File nodes whose blob ID (content hash) appears in
               more than one repository, revealing files with identical
               content shared across different projects.

  - Feature 3: Repository File Count Visualization
               Counts files per repository and renders a horizontal bar
               chart using matplotlib to visualize the most file-rich
               repositories in the dataset.

This module works with file records loaded into Neo4j from Sample_Files.json.
The graph model is:
  (:File {id, path, mode, symlink})-[:BELONGS_TO]->(:Repo {name})
  (:File {id, path, mode, symlink})-[:ON_BRANCH]-> (:Branch {ref})

Depends on neo4j_crud for the driver connection.
Imported by menu.py — do not run this file directly.
"""

import matplotlib.pyplot as plt


# ─────────────────────────────────────────
#  FEATURE 1 — TOP REPOSITORIES BY FILE COUNT
# ─────────────────────────────────────────

def get_top_repos_by_file_count(driver, top_n=10):
    """
    Feature 1: Query Neo4j to find repositories with the most tracked files.
    Traverses the BELONGS_TO relationship from File nodes to Repo nodes
    and counts the number of File nodes connected to each Repo.

    Cypher pattern:
      MATCH (:File)-[:BELONGS_TO]->(r:Repo)
      RETURN r.name, count(*) AS files
      ORDER BY files DESC

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        top_n  (int):          Number of top repositories to return.

    Returns:
        list of tuples: [(repo_name, file_count), ...]
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (:File)-[:BELONGS_TO]->(r:Repo)
            RETURN r.name AS repo, count(*) AS files
            ORDER BY files DESC
            LIMIT $top_n
        """, top_n=top_n)

        return [(record["repo"], record["files"]) for record in result]


def display_top_repos_by_file_count(driver, top_n=10):
    """
    Print the top repositories by file count to the console
    with an ASCII bar chart.

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        top_n  (int):          Number of repositories to display.
    """
    repos = get_top_repos_by_file_count(driver, top_n)

    print(f"\n{'─'*55}")
    print(f"  [Feature 1] Top {top_n} Repositories by File Count")
    print(f"{'─'*55}")

    if not repos:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*55}\n")
        return

    for rank, (repo, count) in enumerate(repos, start=1):
        # Scale ASCII bar to a max of 30 characters
        bar = "█" * min(count, 30)
        print(f"  {rank:>2}. {repo:<40} {count:>5} files  {bar}")

    print(f"{'─'*55}\n")


# ─────────────────────────────────────────
#  FEATURE 2 — SHARED FILE DETECTION ACROSS REPOS
# ─────────────────────────────────────────

def get_shared_files(driver, top_n=10):
    """
    Feature 2: Find File nodes whose blob ID (content hash) appears in
    more than one repository. Since the file ID is a content hash (SHA),
    two File nodes with the same ID have identical content — this reveals
    files that are shared or duplicated across different projects.

    Cypher pattern:
      MATCH (f:File)-[:BELONGS_TO]->(r:Repo)
      WITH f.id, collect(DISTINCT r.name) AS repos
      WHERE size(repos) > 1

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        top_n  (int):          Number of results to return.

    Returns:
        list of tuples: [(file_id, repo_list, repo_count), ...]
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (f:File)-[:BELONGS_TO]->(r:Repo)
            WITH f.id AS file_id,
                 f.path AS path,
                 collect(DISTINCT r.name) AS repos
            WHERE size(repos) > 1
            RETURN file_id, path, repos, size(repos) AS repo_count
            ORDER BY repo_count DESC
            LIMIT $top_n
        """, top_n=top_n)

        return [(r["file_id"], r["path"], r["repos"], r["repo_count"])
                for r in result]


def display_shared_files(driver, top_n=10):
    """
    Print the top shared files (by number of repositories they appear in)
    to the console.

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        top_n  (int):          Number of shared files to display.
    """
    shared = get_shared_files(driver, top_n)

    print(f"\n{'─'*65}")
    print(f"  [Feature 2] Top {top_n} Files Shared Across Multiple Repositories")
    print(f"  (files with identical content found in more than one repo)")
    print(f"{'─'*65}")

    if not shared:
        print("  No shared files found. Load a dataset first (option 1).")
        print(f"{'─'*65}\n")
        return

    for file_id, path, repos, count in shared:
        # Truncate long file IDs for display readability
        short_id = file_id[:12] + "..." if len(file_id) > 12 else file_id
        print(f"\n  File ID : {short_id}")
        print(f"  Path    : {path}")
        print(f"  Found in: {count} repositories")
        for repo in repos[:5]:   # Show up to 5 repos per file
            print(f"    → {repo}")
        if len(repos) > 5:
            print(f"    ... and {len(repos) - 5} more")

    print(f"\n{'─'*65}\n")


# ─────────────────────────────────────────
#  FEATURE 3 — REPOSITORY FILE COUNT VISUALIZATION
# ─────────────────────────────────────────

def visualize_repo_file_counts(driver, top_n=10):
    """
    Feature 3: Render a horizontal bar chart of the top N repositories
    by file count using matplotlib.

    Bars are sorted with the repository containing the most files at the top.
    Repository names are displayed on the Y axis for readability.

    Args:
        driver (neo4j.Driver): Active Neo4j driver.
        top_n  (int):          Number of repositories to visualize.
    """
    data = get_top_repos_by_file_count(driver, top_n)

    if not data:
        print("  No data found. Load a dataset first (option 1).")
        return

    # Unpack and reverse so the highest bar appears at the top
    repos, counts = zip(*data)
    repos  = list(reversed(repos))
    counts = list(reversed(counts))

    # Shorten long repo names (owner/repo) to just the repo part for Y axis
    short_repos = [r.split("/")[-1] if "/" in r else r for r in repos]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(short_repos, counts, color="#E15759", edgecolor="white")

    # Add file count labels at the end of each bar
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9)

    ax.set_title(f"Top {top_n} Repositories by File Count (Sample_Files.json)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Files")
    ax.set_ylabel("Repository")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()
