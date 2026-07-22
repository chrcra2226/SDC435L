"""
sqlite_features.py — Analytical Features
==========================================
Implements the three key analytical features for the GitHub commit
dataset application using SQLite queries and aggregation:

  - Feature 1: Top Repositories by Files Changed
               Queries the commits table and sums the files_changed
               column per repository to rank repos by total file
               activity across all their commits.

  - Feature 2: Most Prolific Authors
               Groups commits by author_name and counts the number
               of commits per author to identify the most active
               contributors in the dataset.

  - Feature 3: Commit Activity Visualization
               Counts commits per repository and renders a horizontal
               bar chart using matplotlib to visualize the most active
               repositories by commit count.

This module works with commit records loaded into SQLite from
Sample_Commits.json. The 'files_changed' column is derived from the
length of the 'difference' array in each raw commit record, which
lists every file modified in that commit.

Depends on sqlite_crud for the connection.
Imported by menu.py — do not run this file directly.
"""

import matplotlib.pyplot as plt


# ─────────────────────────────────────────
#  FEATURE 1 — TOP REPOSITORIES BY FILES CHANGED
# ─────────────────────────────────────────

def get_top_repos_by_files_changed(conn, top_n=10):
    """
    Feature 1: Query SQLite to find the repositories with the highest
    total number of file changes across all their commits. Uses the
    SUM aggregate on the files_changed column grouped by repo_name.

    SQL pattern:
      SELECT repo_name, SUM(files_changed) AS total_files
      FROM commits
      GROUP BY repo_name
      ORDER BY total_files DESC

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of top repositories to return.

    Returns:
        list of tuples: [(repo_name, total_files_changed), ...]
    """
    cursor = conn.execute("""
        SELECT repo_name, SUM(files_changed) AS total_files
        FROM commits
        GROUP BY repo_name
        ORDER BY total_files DESC
        LIMIT ?
    """, (top_n,))

    return [(row["repo_name"], row["total_files"]) for row in cursor.fetchall()]


def display_top_repos_by_files_changed(conn, top_n=10):
    """
    Print the top repositories by total files changed to the console
    with an ASCII bar chart.

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of repositories to display.
    """
    repos = get_top_repos_by_files_changed(conn, top_n)

    print(f"\n{'─'*60}")
    print(f"  [Feature 1] Top {top_n} Repositories by Total Files Changed")
    print(f"{'─'*60}")

    if not repos:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*60}\n")
        return

    for rank, (repo, total) in enumerate(repos, start=1):
        # Scale ASCII bar to a max of 30 characters
        bar = "█" * min(int(total / max(r[1] for r in repos) * 30), 30)
        print(f"  {rank:>2}. {repo:<40} {total:>5} files  {bar}")

    print(f"{'─'*60}\n")


# ─────────────────────────────────────────
#  FEATURE 2 — MOST PROLIFIC AUTHORS
# ─────────────────────────────────────────

def get_top_authors(conn, top_n=10):
    """
    Feature 2: Query SQLite to find the authors with the most commits
    in the dataset. Groups rows by author_name and counts the number
    of commit rows per author.

    SQL pattern:
      SELECT author_name, COUNT(*) AS commit_count
      FROM commits
      GROUP BY author_name
      ORDER BY commit_count DESC

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of top authors to return.

    Returns:
        list of tuples: [(author_name, commit_count), ...]
    """
    cursor = conn.execute("""
        SELECT author_name, COUNT(*) AS commit_count
        FROM commits
        GROUP BY author_name
        ORDER BY commit_count DESC
        LIMIT ?
    """, (top_n,))

    return [(row["author_name"], row["commit_count"]) for row in cursor.fetchall()]


def display_top_authors(conn, top_n=10):
    """
    Print the top authors by commit count to the console
    with an ASCII bar chart.

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of authors to display.
    """
    authors = get_top_authors(conn, top_n)

    print(f"\n{'─'*60}")
    print(f"  [Feature 2] Top {top_n} Most Prolific Authors by Commit Count")
    print(f"{'─'*60}")

    if not authors:
        print("  No data found. Load a dataset first (option 1).")
        print(f"{'─'*60}\n")
        return

    for rank, (author, count) in enumerate(authors, start=1):
        bar = "█" * min(count, 30)
        print(f"  {rank:>2}. {author:<35} {count:>4} commits  {bar}")

    print(f"{'─'*60}\n")


# ─────────────────────────────────────────
#  FEATURE 3 — COMMIT ACTIVITY VISUALIZATION
# ─────────────────────────────────────────

def get_repo_commit_counts(conn, top_n=10):
    """
    Feature 3: Query SQLite for commit counts per repository for
    visualization. Groups by repo_name and counts rows per group.

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of repositories to include.

    Returns:
        list of tuples: [(repo_name, commit_count), ...]
    """
    cursor = conn.execute("""
        SELECT repo_name, COUNT(*) AS commit_count
        FROM commits
        GROUP BY repo_name
        ORDER BY commit_count DESC
        LIMIT ?
    """, (top_n,))

    return [(row["repo_name"], row["commit_count"]) for row in cursor.fetchall()]


def visualize_commit_activity(conn, top_n=10):
    """
    Feature 3: Render a horizontal bar chart of the top N most active
    repositories by commit count using matplotlib.

    Bars are sorted with the most active repository at the top.
    Repository names are displayed on the Y axis for readability
    since they tend to be long strings (owner/repo format).

    Args:
        conn  (sqlite3.Connection): Active SQLite connection.
        top_n (int): Number of repositories to visualize.
    """
    data = get_repo_commit_counts(conn, top_n)

    if not data:
        print("  No data found. Load a dataset first (option 1).")
        return

    # Unpack and reverse so the highest bar appears at the top
    repos, counts = zip(*data)
    repos  = list(reversed(repos))
    counts = list(reversed(counts))

    # Shorten long repo names (owner/repo) to just the repo part
    short_repos = [r.split("/")[-1] if "/" in r else r for r in repos]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(short_repos, counts, color="#59A14F", edgecolor="white")

    # Add commit count labels at the end of each bar
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9)

    ax.set_title(f"Top {top_n} Most Active Repositories (Sample_Commits.json)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Commits")
    ax.set_ylabel("Repository")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()
