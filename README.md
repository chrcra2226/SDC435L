# SDC435L
Lab files
## Project Overview

This Python application integrates with multiple database technologies to store and analyze data from the **GitHub Archive dataset** (`GitHubArchive-Dataset.zip`). 
Each part of the project introduces a new database, building toward a comprehensive understanding of how different data storage systems handle the same real-world data.

This is a five-part group project. **Part 1 (Redis) is fully implemented.** Parts 2–5 are placeholders and will be completed in future weeks.

| Part | Database  | Type                  | Status            |
|------|-----------|-----------------------|-------------------|
| 1    | Redis     | Key-Value (In-Memory) | Complete          |
| 2    | MongoDB   | Document              | Under Construction|
| 3    | Cassandra | Wide-Column           | Under Construction|
| 4    | Neo4j     | Graph                 | Under Construction|
| 5    | SQLite    | Relational            | Under Construction|

---

## Dataset

This application uses **`Commits.json`** from the provided `GitHubArchive-Dataset.zip`. Each line of the file is one JSON object describing a single Git commit, with fields including:

| Field        | Description                                              |
|--------------|------------------------------------------------------------|
| `commit`     | The commit SHA — used as the unique Redis key              |
| `author`     | `{ "name": ..., "email": ... }` — who wrote the commit      |
| `committer`  | `{ "name": ..., "email": ... }` — who committed it          |
| `repo_name`  | A **list** containing the repository name(s), e.g. `["owner/repo"]` |
| `message`    | The full commit message                                    |
| `subject`    | The first line of the commit message                       |
| `parent`     | A list of parent commit SHA(s)                              |
| `tree`       | The tree SHA                                                |

The dataset ZIP also includes several other files (`Files.json`, `Contents.json`, `Languages.json`, `Licenses.json`, and `Sample_*` variants) describing repository file listings, 
file contents, language breakdowns, and license info. These are not used by the current Redis implementation but may be useful for future parts of the project 
(e.g. Languages.json for a MongoDB document-model demo).

---

## Project Structure

```
project/
├── menu.py               # Entry point — main menu and all submenus
├── redis_crud.py         # Redis: connection, data loading, CRUD operations
├── redis_features.py     # Redis: three analytical features
├── README.md             # This file
└── data/
    └── Commits.json       ← extracted from GitHubArchive-Dataset.zip
```

### File Responsibilities

**`menu.py`** — The only file you run. Displays the main database selection menu, routes to each database's submenu, and handles all user input and result display. 
  As new databases are added in future weeks, new submenus will be added here.

**`redis_crud.py`** — All core Redis functionality: establishing the connection, loading JSONL commit data from disk, normalizing the `repo_name` list field, 
  and the four CRUD operations (Create, Read, Update, Delete) keyed on commit SHA. Also imported by `redis_features.py` for the `read_commit()` and `get_repo_name()` helpers.

**`redis_features.py`** — The three analytical features built on top of the Redis data. Imports `redis_crud.read_commit()` and `redis_crud.get_repo_name()`.

---

## Navigation Pathways

### Main Menu
```
python menu.py
│
├── 1. Redis      →  Redis Submenu  (fully implemented)
├── 2. MongoDB    →  "Option under construction" → back to main menu
├── 3. Cassandra  →  "Option under construction" → back to main menu
├── 4. Neo4j      →  "Option under construction" → back to main menu
├── 5. SQLite     →  "Option under construction" → back to main menu
└── 0. Exit
```

### Redis Submenu
```
Redis Menu
│
├── CRUD Operations
│     1. Load & store all commits from file
│     2. Read a specific commit by SHA
│     3. Update a commit field
│     4. Delete a commit by SHA
│     5. List stored commit SHAs
│
├── Features
│     6. [Feature 1] Most active repositories
│     7. [Feature 2] Commit keyword frequency analysis
│     8. [Feature 3] Author contribution history
│     9. [Feature 3] Top contributors leaderboard
│
└── 0. Back to main menu
```

---

## Part 1 — Redis Features

### CRUD Operations
- **Create** — Load commit records from `Commits.json` into Redis individually or in bulk using pipelining for efficiency
- **Read** — Retrieve any stored commit by its unique commit SHA
- **Update** — Modify one or more fields on any stored commit
- **Delete** — Remove a commit from Redis by SHA
- **List** — Scan and display stored commit SHAs

### Analytical Features

**Feature 1 — Most Active Repositories Ranking**
Counts the number of commits per repository (using the first repo name in each commit's `repo_name` list) and stores the result in a Redis Sorted Set (`ranking:repos`). 
Displays a ranked leaderboard of the top N most active repositories with an ASCII bar chart.

**Feature 2 — Commit Message Keyword Frequency Analysis**
The raw dataset has no event-type field, so this feature instead analyzes the leading word of each commit's `subject` line (e.g. "Fix", "Add", "Update", "Merge"), 
which conventionally describes the type of change. Frequencies are tracked in a Redis Sorted Set (`ranking:commit_keywords`) and displayed with counts and percentage share.

**Feature 3 — Author Contribution History Viewer**
Stores each author's commit SHAs in a per-author Redis List (`author:<name>:commits`) and ranks all authors by total commits in a Sorted Set (`ranking:authors`). 
Supports looking up any commit author's recent commit history and displaying a top contributors leaderboard.

---

## Redis Data Model

| Key Pattern              | Redis Type     | Description                                       |
|---------------------------|----------------|----------------------------------------------------|
| `commit:<sha>`             | String (JSON)  | Full commit object stored as serialized JSON       |
| `ranking:repos`            | Sorted Set     | Repository names scored by total commit count      |
| `ranking:commit_keywords`  | Sorted Set     | Commit subject keywords scored by frequency        |
| `author:<name>:commits`    | List           | Ordered list of commit SHAs for a specific author  |
| `ranking:authors`          | Sorted Set     | Author names scored by total commit count          |

---

## Technology Requirements

| Requirement    | Details        |
|----------------|----------------|
| Language       | Python 3.8+    |
| Database       | Redis 6.0+     |
| Python Driver  | `redis-py`     |

---

## Dependencies

Install required Python packages:

```bash
pip install redis
```

Full dependency list:
```
redis>=4.0.0
```

---

## Setup & Running the Application

### 1. Ensure Redis is running

If using a local Redis installation:
```bash
redis-server
```

### 2. Run the application

```bash
python menu.py
```

### 3. Recommended first steps

1. From the main menu, select **1** for Redis
2. Select **option 1** and press Enter to accept the default path (`data/Commits.json`) — this loads all 25,000 commits and builds all indexes automatically (takes under a minute)
3. Select **option 6** to see the most active repositories
4. Select **option 7** to see the commit keyword breakdown
5. Select **option 9** to see the top contributors leaderboard
6. Select **option 8** and enter an author name (e.g. one seen in option 9's results) to view their individual contribution history
7. Enter **0** to return to the main menu when finished

---

## Team Members

- Christopher Crayton, Elvis Ngawe, Michael Winstead

---

## Notes

- All commits are stored as JSON strings under `commit:<sha>` keys in Redis
- Bulk loading uses Redis **pipelining** to batch commands and minimize network round-trips
- Sorted Sets allow O(log N) insertion and O(log N + M) range queries, making ranking operations fast regardless of dataset size
- `repo_name` in the source data is a list (sometimes containing more than one repository name for forked/mirrored repos); the application uses the first entry as the canonical repo name
- The application handles both `.json` (array format) and `.jsonl` (one-object-per-line) dataset formats automatically — `Commits.json` itself is in JSONL format
- `redis_features.py` imports `read_commit()` and `get_repo_name()` from `redis_crud.py` — both files must be in the same directory
