"""
redis_features.py — Analytical Features
==========================================
Implements the three key analytical features for the GitHub commit
dataset application:
  - Feature 1: Most Active Repositories Ranking
  - Feature 2: Commit Message Keyword Frequency Analysis
  - Feature 3: Author Contribution History Viewer

This module works with commit records loaded from Commits.json. Each
commit has an author name, a repo_name (stored as a list in the source
data — see redis_crud.get_repo_name), and a commit subject/message.

Depends on redis_crud for read_commit() and get_repo_name().
Imported by menu.py — do not run this file directly.
"""

from collections import defaultdict
import redis_crud


# ─────────────────────────────────────────
#  FEATURE 1 — MOST ACTIVE REPOSITORIES
# ─────────────────────────────────────────

def build_repo_activity_index(client, commits):
    """
    Feature 1: Index repositories into a Redis Sorted Set ranked by
    total commit count. Uses ZINCRBY so repeated loads accumulate correctly.

    Redis key: ranking:repos  (Sorted Set)
      Member → repository full name (e.g. 'torvalds/linux')
      Score  → total number of commits for that repo

    Args:
        client (redis.Redis): Active Redis client.
        commits (list): List of commit dictionaries.
    """
    print("\n[Feature 1] Building repository activity index...")
    repo_counts = defaultdict(int)

    for commit in commits:
        repo = redis_crud.get_repo_name(commit)
        if repo:
            repo_counts[repo] += 1

    pipe = client.pipeline()
    for repo, count in repo_counts.items():
        pipe.zincrby("ranking:repos", count, repo)
    pipe.execute()

    print(f"[OK] Indexed {len(repo_counts)} repositories.")


def get_top_repos(client, top_n=10):
    """
    Return the top N repositories by commit count from the Redis Sorted Set.

    Args:
        client (redis.Redis): Active Redis client.
        top_n (int): Number of top results to return.

    Returns:
        list of tuples: [(repo_name, commit_count), ...]
    """
    results = client.zrevrange("ranking:repos", 0, top_n - 1, withscores=True)
    return [(repo, int(score)) for repo, score in results]


# ─────────────────────────────────────────
#  FEATURE 2 — COMMIT MESSAGE KEYWORD FREQUENCY
# ─────────────────────────────────────────

def build_commit_keyword_index(client, commits):
    """
    Feature 2: Index the leading keyword of each commit subject line into
    a Redis Sorted Set ranked by frequency. Commit subjects conventionally
    start with an action word (Fix, Add, Update, Merge, Remove, etc.),
    so this surfaces the most common types of changes in the dataset.

    Redis key: ranking:commit_keywords  (Sorted Set)
      Member → the first word of the commit subject, capitalized
               (e.g. 'Fix', 'Add', 'Merge', 'Update')
      Score  → number of commits whose subject starts with that word

    Args:
        client (redis.Redis): Active Redis client.
        commits (list): List of commit dictionaries.
    """
    print("\n[Feature 2] Building commit message keyword index...")
    keyword_counts = defaultdict(int)

    for commit in commits:
        subject = (commit.get("subject") or "").strip()
        if not subject:
            continue
        words = subject.split()
        if not words:
            continue
        # Use the first word of the subject as the "keyword", stripping
        # a trailing colon (e.g. "Fix:" -> "Fix") and normalizing case.
        keyword = words[0].rstrip(":").capitalize()
        if keyword:
            keyword_counts[keyword] += 1

    pipe = client.pipeline()
    for keyword, count in keyword_counts.items():
        pipe.zincrby("ranking:commit_keywords", count, keyword)
    pipe.execute()

    print(f"[OK] Indexed {len(keyword_counts)} distinct commit keywords.")


def get_commit_keyword_frequencies(client, top_n=15):
    """
    Return the top N commit subject keywords and their frequencies,
    ranked highest first.

    Args:
        client (redis.Redis): Active Redis client.
        top_n (int): Number of top keywords to return.

    Returns:
        list of tuples: [(keyword, count), ...]
    """
    results = client.zrevrange("ranking:commit_keywords", 0, top_n - 1, withscores=True)
    return [(kw, int(score)) for kw, score in results]


# ─────────────────────────────────────────
#  FEATURE 3 — AUTHOR CONTRIBUTION HISTORY
# ─────────────────────────────────────────

def build_author_contribution_index(client, commits):
    """
    Feature 3: Index author contributions using two Redis structures:
      - A List per author storing their commit SHAs in arrival order
      - A Sorted Set ranking all authors by total commit count

    Redis keys:
      author:<name>:commits  (List)       → ordered commit SHAs for this author
      ranking:authors        (Sorted Set) → author name scored by total commits

    Args:
        client (redis.Redis): Active Redis client.
        commits (list): List of commit dictionaries.
    """
    print("\n[Feature 3] Building author contribution index...")
    author_commit_map = defaultdict(list)

    for commit in commits:
        author_name = commit.get("author", {}).get("name")
        commit_sha = commit.get("commit")
        if author_name and commit_sha:
            author_commit_map[author_name].append(commit_sha)

    pipe = client.pipeline()
    for author_name, shas in author_commit_map.items():
        list_key = f"author:{author_name}:commits"
        for sha in shas:
            pipe.rpush(list_key, sha)                              # Append to author's commit list
        pipe.zincrby("ranking:authors", len(shas), author_name)    # Increment author score
    pipe.execute()

    print(f"[OK] Indexed contributions for {len(author_commit_map)} authors.")


def get_author_contribution_history(client, author_name, limit=10):
    """
    Retrieve an author's most recent commits and their total commit count.
    Calls redis_crud.read_commit() to fetch full commit data for each SHA.

    Args:
        client (redis.Redis): Active Redis client.
        author_name (str): Author name to look up (matches 'author.name').
        limit (int): Maximum number of recent commits to return.

    Returns:
        dict: {
            'author_name'   : str,
            'total_commits' : int,
            'recent_commits': list of commit dicts (most recently loaded first)
        }
    """
    list_key = f"author:{author_name}:commits"
    commit_shas = client.lrange(list_key, -limit, -1)  # Grab the last N SHAs
    total = client.llen(list_key)

    recent_commits = []
    for sha in reversed(commit_shas):  # Reverse so most recently loaded appears first
        commit = redis_crud.read_commit(client, sha)
        if commit:
            recent_commits.append(commit)

    return {
        "author_name": author_name,
        "total_commits": total,
        "recent_commits": recent_commits
    }


def get_top_contributors(client, top_n=10):
    """
    Return the top N contributing authors by total commit count.

    Args:
        client (redis.Redis): Active Redis client.
        top_n (int): Number of top contributors to return.

    Returns:
        list of tuples: [(author_name, commit_count), ...]
    """
    results = client.zrevrange("ranking:authors", 0, top_n - 1, withscores=True)
    return [(author, int(score)) for author, score in results]
