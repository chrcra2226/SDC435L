"""
mongodb_features.py
=============================
MongoDB analytics features
Dataset: sample_repos.json
Schema: repo_name, watch_count
"""

# -----------------------------------------------------
# FEATURE 1: REPOSITORY NAME LENGTH ANALYSIS
# -----------------------------------------------------

def display_repo_name_lengths(collection):
    """
    Display the longest and shortest repository names
    stored in the MongoDB collection.
    """

    # Stop if the collection is not available
    if collection is None:
        return

    # Retrieve only the repository names
    repos = list(collection.find({}, {"repo_name": 1, "_id": 0}))

    # Extract repository names into a list
    names = [r.get("repo_name", "") for r in repos]

    # Check whether any repository names were found
    if not names:
        print("No data found")
        return

    # Find the longest and shortest repository names
    longest = max(names, key=len)
    shortest = min(names, key=len)

    # Display the results
    print("\n=== Repository Name Analysis ===")
    print(f"Longest repo name: {longest}")
    print(f"Shortest repo name: {shortest}")


# -----------------------------------------------------
# FEATURE 2: TOP WATCHED REPOSITORIES
# -----------------------------------------------------

def display_top_repositories(collection):
    """
    Display the ten repositories with the highest watch counts.
    """

    # Stop if the collection is not available
    if collection is None:
        return

    # Aggregation pipeline:
    # 1. Sort repositories by watch_count (highest first)
    # 2. Return only the top 10 repositories
    pipeline = [
        {"$sort": {"watch_count": -1}},
        {"$limit": 10}
    ]

    # Execute the aggregation query
    results = list(collection.aggregate(pipeline))

    print("\n=== Top Repositories by Watch Count ===")

    # Display each repository with a simple bar chart
    for i, r in enumerate(results, 1):

        # Get repository information
        repo = r.get("repo_name", "Unknown")
        watch = r.get("watch_count", 0)

        # Create a scaled bar to visualize watch count
        bar = "█" * min(watch // 2, 30)

        # Print repository ranking
        print(f"{i}. {repo:<35} {watch:<6} {bar}")


# -----------------------------------------------------
# FEATURE 3: WATCH COUNT STATISTICS
# -----------------------------------------------------

def display_watch_statistics(collection):
    """
    Calculate and display statistics about repository watch counts.
    """

    # Stop if the collection is not available
    if collection is None:
        return

    # Retrieve only the watch_count field
    repos = list(collection.find({}, {"watch_count": 1, "_id": 0}))

    # Store watch counts in a list
    values = [r.get("watch_count", 0) for r in repos]

    # Check whether data exists
    if not values:
        print("No data found")
        return

    # Calculate the average watch count
    avg = sum(values) / len(values)

    # Count repositories above the average
    above = sum(1 for v in values if v > avg)

    # Count repositories below or equal to the average
    below = len(values) - above

    # Display the statistics
    print("\n=== Watch Count Analysis ===")
    print(f"Average watch count: {avg:.2f}")
    print(f"Above average: {above}")
    print(f"Below average: {below}")


# -----------------------------------------------------
# OPTIONAL: TOTAL REPOSITORIES
# -----------------------------------------------------

def get_total_repositories(collection):
    """
    Return the total number of repositories stored
    in the MongoDB collection.
    """

    # Return zero if the collection is unavailable
    if collection is None:
        return 0

    # Count all documents in the collection
    return collection.count_documents({})
