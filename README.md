# SDC435L
Lab files for the class group project.
## Project Overview


This Python application integrates with multiple database technologies to store and analyze data from the GitHub Archive dataset (GitHubArchive-Dataset.zip). Each part of the project introduces a new database, building toward a comprehensive understanding of how different data storage systems handle the same real-world data.

This is a five-part group project with all five parts being fully implemented

| Part | Database  | Type                  | Status            |
|------|-----------|-----------------------|-------------------|
| 1    | Redis     | Key-Value (In-Memory) | Complete          |
| 2    | MongoDB   | Document              | Complete          |
| 3    | Cassandra | Wide-Column           | Complete          |
| 4    | Neo4j     | Graph                 | Complete          |
| 5    | SQLite    | Relational            | Complete          |


### Dataset
Each database uses a different file from the GitHubArchive-Dataset.zip:

|Database  |File             |Description|
|----------|-------------------|--------------------------------------------|
|Redis     |Commits.json       |GitHub commit records (SHA, author, message)|
|MongoDB   |Sample_Repos.json  |GitHub repository records (name, watch count)|
|Cassandra |Licenses.json      |Repository license records (repo name, license)|
|Neo4j     |Sample_Files.json  |Repository file records (path, blob ID, branch)|
|SQLite    |Sample_Commits.json|GitHub commit records with file change details (SHA, author, repo, files changed)|

This application uses multiple .json files from the provided GitHubArchive-Dataset.zip. Each line of the files is one JSON object describing a single dataset, with fields including:

#### Commits.json Fields (Redis)

| Field        | Description                                                         |
|--------------|---------------------------------------------------------------------|
| `commit`     | The commit SHA — used as the unique Redis key                       |
| `author`     | `{ "name": ..., "email": ... }` — who wrote the commit              |
| `committer`  | `{ "name": ..., "email": ... }` — who committed it                  |
| `repo_name`  | A **list** containing the repository name(s), e.g. `["owner/repo"]` |
| `message`    | The full commit message                                             |
| `subject`    | The first line of the commit message                                |
| `parent`     | A list of parent commit SHA(s)                                      |
| `tree`       | The tree SHA                                                        |

#### Sample_Repos.json Fields (MongoDB)

| Field           | Description                                        |
|-----------------|----------------------------------------------------|
| `repo_name`     | Full repository name (e.g. `owner/repo`            |
| `watch_count`   | Number of users watching the repositories          |
| `language`      | Primary programming language of the repositories   |
| `commits`       | Total number of commits in the repository          |

#### Licenses.json Fields (Cassandra)

| Field           | Description                                            |
|-----------------|--------------------------------------------------------|
| `repo_name`     | The repository the file belongs to (e.g. `owner/repo`) |
| `license`       | The license type associated with the repository        |

#### Sample_Files.json Fields (Neo4j)

| Field           | Description                                                |
|-----------------|------------------------------------------------------------|
| `id`            | The blob SHA - Unique identifier for the file content      |
| `repo_name`     | The repository the file belongs to (e.g. `owner/repo`)     |
| `ref`           | The git branch refernce (e.g. `refs/heads/master`)         |
| `path`          | The file path within the repository                        |
| `mode`          | The file mode (e.g. `33188` for a regular file)            |
| `symlink_target`| Symlink destination if the file is a symlink, else absent  |

#### Sample_Commits.json Fields (SQLite)

| Field        | Description                                                         |
|--------------|---------------------------------------------------------------------|
| `commit`     | The commit SHA — used as the unique Redis key                       |
| `author`     | `{ "name": ..., "email": ... }` — who wrote the commit              |
| `committer`  | `{ "name": ..., "email": ... }` — who committed it                  |
| `repo_name`  | The repository name as a plain string (e.g. `owner/repo`) |
| `message`    | The full commit message                                             |
| `subject`    | The first line of the commit message                                |
| `difference` | List of file changes — each entry has new_path, old_path, new_mode, old_mode|
| `tree`       | The tree SHA                                                        |

The dataset ZIP also includes all files used within the application and more (Files.json, Contents.json, Languages.json, Licenses.json, and Sample_* variants) that describe repository file listings, file contents, language breakdowns, and license info.

### Project Structure

project/

├── menu.py               # Entry point — main menu and all submenus

├── redis_crud.py         # Redis: connection, data loading, CRUD operations

├── redis_features.py     # Redis: three analytical features

├── mongodb_crud.py       # MongoDB: CRUD operations 

├── mongodb_features.py   # MongoDB: three analytical features 

├── Cassandra.py          # Cassandra: Functionality (Both CRUD and 3 features)

├── MenuCassandra.py      # Cassandra: Menu display

├── neo4j_crud.py         # Neo4j: connection, data loading, CRUD operations

├── neo4j_features.py     # Neo4j: three analytical features

├── sqlite_crud.py        # SQLite: connection, data loading, CRUD operations

├── sqlite_features.py    # SQLite: three analytical features

├── README.md             # This file

└── data/

---├── Commits.json       # Redis dataset (GitHub commits)

---├── Licenses.json      # Cassandra dataset (GitHub Licenses)
    
---├── Sample_repos.json  # MongoDB dataset (repositories)

---├── Sample_Files.json  # Neo4j dataset (repository files)

---├── Sample_Commits.json # SQLite dataset (GitHub commits with file changes)

---└── databases/

------└── github_archive.db # SQLite database file (auto-created on first run)

### File Responsibilities

menu.py — The only file you run. Displays the main database selection menu, routes to each database's submenu, and handles all user input and result display. As new databases are added in future weeks, new submenus are added here.

redis_crud.py — All core Redis functionality: establishing the connection, loading JSONL commit data from disk, normalizing the repo_name list field, and the four CRUD operations (Create, Read, Update, Delete) keyed on commit SHA. Also imported by redis_features.py for helper functions.

redis_features.py — The three analytical features built on top of Redis data. Uses Redis sorted sets and lists to generate repository, keyword, and author analytics.

mongodb_crud.py — Handles MongoDB connection, dataset loading, and CRUD operations using PyMongo. Stores repository-level documents in a MongoDB collection.

mongodb_features.py — Implements analytical queries using MongoDB aggregation pipelines.

Cassandra.py — Handles Cassandra connection, keyspace and table creation, data loading from Licenses.json, and all CRUD and analytical operations for the Cassandra submenu.

MenuCassandra.py - Handles the menu functionality for Cassandra section

neo4j_crud.py — Handles Neo4j driver connection, data loading from Sample_Files.json, and all four CRUD operations. Creates File, Repo, and Branch nodes with BELONGS_TO and ON_BRANCH relationships using MERGE to prevent duplicates.

neo4j_features.py — Implements the three analytical features using Neo4j graph traversal: top repositories by file count, shared file detection across repositories, and a matplotlib bar chart visualization of repository file counts.

sqlite_crud.py — Handles SQLite database creation and schema setup using Python's built-in sqlite3 module. Loads commit data from Sample_Commits.json and performs all four CRUD operations on the commits table. The files_changed column is derived from the length of the difference array in each commit record.

sqlite_features.py — Implements the three analytical features using SQL aggregation: top repositories by total files changed, most prolific authors by commit count, and a matplotlib bar chart of commit activity per repository.

### Navigation Pathways

#### Main Menu

python menu.py

│

├── 1. Redis      → Redis Submenu (fully implemented)

├── 2. MongoDB    → MongoDB Submenu (fully implemented)

├── 3. Cassandra  → Cassandra Submenu (fully implemented)

├── 4. Neo4j      → "Neo4j Submenu (fully implemented)"

├── 5. SQLite     → "SQLite Submenu (fully implemented)"

└── 0. Exit

#### Redis Submenu

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

│     6. Most active repositories

│     7. Commit keyword frequency analysis

│     8. Author contribution history

│     9. Top contributors leaderboard

│

└── 0. Back to main menu

#### MongoDB Submenu

MongoDB Menu

│

├── CRUD Operations

│     1. Load & store all repository documents from file

│     2. Read repository by name

│     3. Update repository fields

│     4. Delete repository by name

│

├── Features

│     5. Top watched repositories

│     6. Language distribution analysis

│     7. Repository activity summary (commits vs watch count)

│

└── 0. Back to main menu

#### Cassandra Submenu

Cassandra Menu

│

├── CRUD Operations

│     1. Create Repository

│     2. Read Repository

│     3. Update Repository

│     4. Delete Repository

│

├── Analytics

│     5. License Distribution

│     6. Search by License

│     7. Visualize Top Licenses

│

├── System

│     8. Show Record Count

│     9. Exit

│

└── Back to main menu

Neo4j Menu

│

├── CRUD Operations

│     1. Load & store all files from Sample_Files.json

│     2. Read a specific file by blob ID

│     3. Update a file property

│     4. Delete a file by blob ID

│     5. List stored files

│

├── Features

│     6. Top repositories by file count

│     7. Shared files across repositories

│     8. Visualize repository file counts

│

└── 0. Back to main menu

#### SQLite Submenu

SQLite Menu

│

├── CRUD Operations

│ 1. Load & store all commits from Sample_Commits.json

│ 2. Read a specific commit by SHA

│ 3. Update a commit field

│ 4. Delete a commit by SHA

│ 5. List stored commits

│

├── Features

│ 6. Top repositories by files changed

│ 7. Most prolific authors

│ 8. Visualize commit activity

│

└── 0. Back to main menu

## Part 1 — Redis Features

### CRUD Operations

Create — Load commit records from Commits.json into Redis using pipelining for efficiency

Read — Retrieve commits by SHA

Update — Modify stored commit fields

Delete — Remove commits by SHA

List — Scan stored commit SHAs

### Analytical Features

Feature 1 — Most Active Repositories
Counts commits per repository and stores results in a Redis Sorted Set. Displays a ranked leaderboard.

Feature 2 — Commit Keyword Frequency
Analyzes the first word of commit subject lines (e.g. Fix, Add, Update) and stores frequency in a Sorted Set.

Feature 3 — Author Contribution History
Tracks author commit activity using Redis lists and sorted sets to show top contributors and history.

### Redis Data Model

| Key Pattern              | Redis Type     | Description                                       |
|---------------------------|----------------|----------------------------------------------------|
| `commit:<sha>`             | String (JSON)  | Full commit object stored as serialized JSON       |
| `ranking:repos`            | Sorted Set     | Repository names scored by total commit count      |
| `ranking:commit_keywords`  | Sorted Set     | Commit subject keywords scored by frequency        |
| `author:<name>:commits`    | List           | Ordered list of commit SHAs for a specific author  |
| `ranking:authors`          | Sorted Set     | Author names scored by total commit count          |

---

### Redis Technology Requirements

| Requirement    | Details        |
|----------------|----------------|
| Language       | Python 3.8+    |
| Database       | Redis 6.0+     |
| Python Driver  | `redis-py`     |


## Part 2 — MongoDB Features

### CRUD Operations

Create — Insert repository documents into MongoDB collection

Read — Query repositories by name, language, or metrics

Update — Modify repository attributes (watch_count, commits, language)

Delete — Remove repository documents by name

### Analytical Features

Feature 1 — Top Watched Repositories
Uses MongoDB aggregation pipeline to rank repositories by watch_count

Feature 2 — Language Distribution
Groups repositories by programming language and counts occurrences

Feature 3 — Repository Activity Summary
Compares commits vs watch_count to evaluate repository engagement

### MongoDB Data Model

Collection: `repositories`

Each document includes:

| Field        | Type   | Description                              |
|--------------|--------|------------------------------------------|
| `repo_name`  | String | Full repository name (e.g. owner/repo)   |
| `watch_count`| String | Number of users watching the repository  |
| `language`   | String | Primary programming language of the repo |
| `commits`    | String | Total number of commits in the repository|

---

### MongoDB Technology Stack

| Component      | Details                              |
|----------------|--------------------------------------|
| Database       | MongoDB 6.0+                         |
| Python Driver  | `pymongo`                            |
| Storage Model  | Document-based NoSQL storage         |
| Analytics      | Aggregation pipelines for analytics  |

## Part 3 — Cassandra Features

### CRUD Operations

Create — Insert repository and license records into Cassandra from Licenses.json

Read — Query repositories by name from the repositories table

Update — Modify repository license values by repo name

Delete — Remove repository records by repo name

### Analytical Features

Feature 1 — License Distribution

Queries all license values from the repositories table and uses Python Counter to rank the top 10 most common licenses.

Feature 2 — Search by License

Prompts the user for a license name and returns all repositories using that license, along with a total count.

Feature 3 — Visualize Top Licenses

Uses matplotlib to render a bar chart of the top 10 most common licenses across all stored repositories.

### Cassandra Data Model

Keyspace: github_license_db

Table: repositories

| Field        | Type   | Description                                   |
|--------------|--------|-----------------------------------------------|
| `id`         | uuid   | Auto-generated unique identifier (PRIMARY KEY)|
| `repo_name`  | String | Full repository name (e.g. owner/repo)        |
| `license`    | String | License type associated with the repository   |

### Cassandra Technology Stack

| Component      | Details                              |
|----------------|--------------------------------------|
| Database       | Cassandra 4.0+Python                 |
| Python Driver  | `cassandra-driver`                   |
| Storage Model  | Wide-column NoSQL storage            |
| Analytics      | Python-side aggregation with Counter |

## Part 4 — Neo4j Features

### CRUD Operations

Create — Load file records from Sample_Files.json and store them as a graph with File, Repo, and Branch nodes

Read — Retrieve a specific file node and its connected Repo and Branch nodes by blob ID

Update — Modify a property on an existing File node by blob ID

Delete — Remove a File node and all its relationships by blob ID

List — Display stored file IDs and their paths from the graph

### Analytical Features

Feature 1 — Top Repositories by File Count
Traverses (:File)-[:BELONGS_TO]->(:Repo) relationships to rank repositories by the number of tracked files they contain.

Feature 2 — Shared File Detection Across Repositories
Finds File nodes whose blob ID (content hash) appears in more than one repository, revealing files with identical content shared across different projects. This is a uniquely graph-friendly query that would be expensive in a relational database.

Feature 3 — Repository File Count Visualization
Uses matplotlib to render a horizontal bar chart of the top N most file-rich repositories in the dataset.

### Neo4j Data Model

#### Nodes:

Label |Properties             |Description
|------|-----------------------|-------------------------------------|
|File  |id, path, mode, symlink|A file tracked in a GitHub repository|
|Repo  |name                   |A GitHub repository                  |
|Branch|ref                    |A git branch reference               |

#### Relationships:

|Relationship|From|To    |Description                       |
|------------|----|------|----------------------------------|
|BELONGS_TO  |File|Repo  |The file exists in this repository|
|ON_BRANCH   |File|Branch|The file is on this branch        |


### Neo4j Technology Stack

| Component      | Details                                  |
|----------------|------------------------------------------|
| Database       | Neo4j 5.0+ (Desktop or Community Edition)|
| Python Driver  | `neo4j`                                  |
| Storage Model  | Graph (nodes and directed relationships) |
| Analytics      | Cypher graph traversal + matplotlib      |

## Part 5 — SQLite Features

### CRUD Operations

Create — Load commit records from Sample_Commits.json into the SQLite commits table using batch inserts

Read — Retrieve a single commit row by SHA including repo, author, subject, and files changed count

Update — Modify any non-primary-key column on an existing commit row by SHA

Delete — Remove a commit row from the commits table by SHA

List — Display stored commit SHAs and their subjects

### Analytical Features

Feature 1 — Top Repositories by Files Changed Queries the commits table using SUM(files_changed) grouped by repo_name to rank repositories by total file activity across all their commits.

Feature 2 — Most Prolific Authors Groups commits by author_name and counts the number of commits per author to identify the most active contributors in the dataset.

Feature 3 — Commit Activity Visualization Uses matplotlib to render a horizontal bar chart of the top N most active repositories by commit count.

## SQLite Data Model

Database file: data/databases/github_archive.db

Table: commits

| Field          | Type    | Description                                               |
|----------------|---------|-----------------------------------------------------------|
| `sha`          | TEXT    | Commit SHA — unique primary key                           |
| `repo_name`    | TEXT    | Full repository name (e.g. owner/repo)                    |
| `author_name`  | TEXT    | Name of the commit author                                 |
| `author_email` | TEXT    | Email of the commit author                                |
| `subject`      | TEXT    | First line of the commit message                          |
| `message`      | TEXT    | Full commit message                                       |
| `tree`         | TEXT    | The tree SHA                                              |
| `files_changed`| INTEGER | Number of files changed — derived from difference array   |

## SQLite Technology Stack

| Component      | Details                                  |
|----------------|------------------------------------------|
| Database       | SQLite 3 (built into Python)             |
| Python Driver  | sqlite3 (Python standard library)        |
| Storage Model  | Relational table with SQL aggregation    |
| Analytics      | SQL GROUP BY + SUM/COUNT + matplotlib    |

## Dependencies

### Install required packages:

pip install redis

pip install pymongo

pip install cassandra-driver

pip install neo4j

pip install matplotlib

No additional install needed for SQLite — sqlite3 is built into Python 3

## Setup & Running the Application

### 1. Start database servers

#### Redis And MongoDB:

Servers connect when corresponding database is selected.

#### Cassandra (Ubuntu only):

`sudo systemctl start cassandra`

#### Neo4j:

Windows — Start the database in Neo4j Desktop and ensure status shows "Started"

Ubuntu — `sudo systemctl start neo4j` if installed on OS

#### SQLite:

No server required — the database file is created automatically at data/databases/github_archive.db on first run.

### 2. Run application from within Project folder

`cd SDC435L-main/Project`

`python3 menu.py`

## Recommended Workflow

### Redis:

- Select option 1
- Select option 1 on Redis Menu
- Loads Commits.json
- Run CRUD and analytic features (options 2–9)

### MongoDB:

- Select option 2
- Select option 1 on MongoDB Menu
- Loads Sample_repos.json
- Run CRUD and analytics features (options 2-8)

### Cassandra:

- Select option 3
- Licenses.json is loaded automatically on startup
- Run CRUD operations (options 1-4)
- Run analytics features (options 5-7)
- View record count (option 8)

### Neo4j:

- Ensure Neo4j server is running before selecting this option
- Select option 4
- Enter connection details when prompted (URI, username, password)
- Select option 1 to load Sample_Files.json into the graph
- Run CRUD operations (options 2–5)
- Run analytics features (options 6–8)

### SQLite:

- Select option 5
- Select option 1 to load Sample_Commits.json into the SQLite database
- Run CRUD operations (options 2–5)
- Run analytics features (options 6–8)
- Database file is saved automatically at data/databases/github_archive.db

## Team Members

Christopher Crayton, Elvis Ngawe, Michael Winstead

## Notes

- Redis uses JSON string storage with sorted sets for analytics
- MongoDB uses document storage with aggregation pipelines
- Cassandra uses a wide-column keyspace with uuid primary keys and Python-side analytics
- Neo4j uses a graph model with directed relationships between File, Repo, and Branch nodes
- Both Redis and MongoDB analyze GitHub commit and repository data; Cassandra analyzes repository license data
- SQLite uses Python's built-in sqlite3 module — no server or driver install required
- The SQLite database is stored as a local file at data/databases/github_archive.db
- All five database integrations are now complete
