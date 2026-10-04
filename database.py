"""
database.py - SQLite database management for cpmeta.
Handles schema initialization, CRUD operations, and compact aggregation
of historical sessions for LLM cumulative analysis.
"""

import json
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "cpmeta.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the SQLite database schema if not present."""
    # Seamless migration from legacy cpnotes.db if present
    if db_path == "cpmeta.db" and not os.path.exists("cpmeta.db") and os.path.exists("cpnotes.db"):
        try:
            shutil.copy("cpnotes.db", "cpmeta.db")
        except Exception:
            pass

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                platform TEXT NOT NULL,
                problem_title TEXT NOT NULL,
                problem_statement TEXT NOT NULL,
                raw_notes TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                solved BOOLEAN NOT NULL DEFAULT 1,
                time_taken_minutes INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Create indices for quick lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON sessions(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_solved ON sessions(solved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON sessions(created_at)")
        conn.commit()


def save_session(
    platform: str,
    problem_title: str,
    problem_statement: str,
    raw_notes: str,
    analysis_json: str,
    solved: bool,
    time_taken_minutes: int,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Inserts a newly analyzed session into the database.
    Returns the newly inserted session ID.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (
                created_at,
                platform,
                problem_title,
                problem_statement,
                raw_notes,
                analysis_json,
                solved,
                time_taken_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                platform.strip(),
                problem_title.strip(),
                problem_statement.strip(),
                raw_notes.strip(),
                analysis_json.strip() if isinstance(analysis_json, str) else json.dumps(analysis_json),
                1 if solved else 0,
                int(time_taken_minutes),
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0


def get_all_sessions(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all sessions ordered by most recent first."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, platform, problem_title, problem_statement,
                   raw_notes, analysis_json, solved, time_taken_minutes
            FROM sessions
            ORDER BY created_at DESC, id DESC
            """
        )
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            d = dict(row)
            d["solved"] = bool(d["solved"])
            try:
                d["analysis"] = json.loads(d["analysis_json"])
            except Exception:
                d["analysis"] = {}
            sessions.append(d)
        return sessions


def get_session_by_id(session_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single session by its integer ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, platform, problem_title, problem_statement,
                   raw_notes, analysis_json, solved, time_taken_minutes
            FROM sessions
            WHERE id = ?
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["solved"] = bool(d["solved"])
        try:
            d["analysis"] = json.loads(d["analysis_json"])
        except Exception:
            d["analysis"] = {}
        return d


def delete_session(session_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Deletes a session by ID. Returns True if a record was removed."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_cumulative_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Aggregates historical sessions into a dense, high-signal summary
    specifically structured to fit efficiently within local LLM context limits.
    """
    sessions = get_all_sessions(db_path)
    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            "session_count": 0,
            "solved_count": 0,
            "unsolved_count": 0,
            "total_time_minutes": 0,
            "condensed_log": "No historical practice sessions found.",
            "topics_tackled": [],
            "stall_causes": [],
        }

    solved_count = sum(1 for s in sessions if s["solved"])
    unsolved_count = total_sessions - solved_count
    total_time = sum(s["time_taken_minutes"] for s in sessions)

    condensed_sessions = []
    all_topics = []
    all_stall_causes = []

    for s in sessions:
        analysis = s.get("analysis", {})
        prob_analysis = analysis.get("problem_analysis", {})
        thinking = analysis.get("thinking_analysis", {})
        recs = analysis.get("recommendations", {})

        core_topics = prob_analysis.get("core_topics", [])
        all_topics.extend(core_topics)

        stall_points = thinking.get("stall_points", [])
        stalls_compact = []
        for sp in stall_points:
            cause = sp.get("root_cause", "")
            if cause:
                all_stall_causes.append(cause)
            stalls_compact.append(
                f"[{sp.get('timestamp_range', '?')}, {sp.get('duration_minutes', 0)}m stall: {sp.get('description', '')} -> Cause: {cause}]"
            )

        condensed_sessions.append(
            {
                "id": s["id"],
                "platform": s["platform"],
                "title": s["problem_title"],
                "solved": s["solved"],
                "time_minutes": s["time_taken_minutes"],
                "core_topics": core_topics,
                "difficulty": prob_analysis.get("difficulty_tier", "Unknown"),
                "key_insight": prob_analysis.get("key_insight", ""),
                "stalls": stalls_compact,
                "behavioral_observations": thinking.get("behavioral_observations", []),
                "topics_to_strengthen": recs.get("topics_to_strengthen", []),
            }
        )

    # Format into a clean, text-based log block optimized for prompt injection
    lines = [
        f"TOTAL SESSIONS: {total_sessions} | SOLVED: {solved_count} | UNSOLVED: {unsolved_count} | TOTAL TIME: {total_time} min",
        "--- SESSION SUMMARIES (Recent to Oldest) ---",
    ]

    for item in condensed_sessions:
        outcome = "SOLVED" if item["solved"] else "FAILED/GAVE UP"
        lines.append(
            f"Session #{item['id']} [{item['platform']}]: '{item['title']}' ({outcome} in {item['time_minutes']} min, Diff: {item['difficulty']})"
        )
        if item["core_topics"]:
            lines.append(f"  Topics: {', '.join(item['core_topics'])}")
        if item["key_insight"]:
            lines.append(f"  Key Insight: {item['key_insight']}")
        if item["stalls"]:
            lines.append(f"  Stalls: {' | '.join(item['stalls'])}")
        if item["behavioral_observations"]:
            lines.append(f"  Observed Behaviors: {' ; '.join(item['behavioral_observations'])}")
        if item["topics_to_strengthen"]:
            lines.append(f"  Recommended Topics: {', '.join(item['topics_to_strengthen'])}")
        lines.append("")

    return {
        "session_count": total_sessions,
        "solved_count": solved_count,
        "unsolved_count": unsolved_count,
        "total_time_minutes": total_time,
        "condensed_log": "\n".join(lines),
        "topics_tackled": list(set(all_topics)),
        "stall_causes": list(set(all_stall_causes)),
        "sessions_raw": condensed_sessions,
    }


def seed_sample_sessions(db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Seeds 3 realistic sample competitive programming sessions
    so the user can immediately test all pages (including cumulative analysis).
    """
    samples = [
        {
            "platform": "LeetCode",
            "problem_title": "437. Path Sum III",
            "problem_statement": "Given the root of a binary tree and an integer targetSum, return the number of paths where the sum of the values along the path equals targetSum. The path does not need to start or end at the root or a leaf, but it must go downwards (i.e., traveling only from parent nodes to child nodes). Constraints: Node values can be negative, up to 1000 nodes.",
            "raw_notes": "0:00 - read problem. binary tree with downward paths.\n0:02 - naive thought: DFS from every node, run sub-DFS. O(N^2) or O(N log N) balanced.\n0:05 - wait, negative numbers exist, so cannot do two-pointer window.\n0:09 - stuck: how to handle prefix sums on trees without recalculating?\n0:15 - remembered Tree Prefix Sum with Hash Map pattern (running sum in map)!\n0:19 - coding recursive DFS. pass prefix_sum, check (prefix_sum - targetSum) in map.\n0:23 - bug on backtrack: forgot to decrement count in map when popping back from child branch.\n0:27 - fixed backtrack decrement. all sample tests passed. submitted -> Accepted.",
            "solved": True,
            "time_taken_minutes": 27,
            "analysis": {
                "problem_analysis": {
                    "core_topics": ["Binary Trees", "Prefix Sums", "Hash Map", "Backtracking / DFS"],
                    "difficulty_tier": "Medium (Rating ~1600)",
                    "key_insight": "Translating the 1D subarray sum equals K prefix sum + hash map technique into tree DFS with state rollback on backtrack."
                },
                "thinking_analysis": {
                    "correct_moves": [
                        "Quickly ruled out two-pointer approach due to presence of negative numbers",
                        "Recalled 1D subarray sum prefix map archetype and mapped it onto tree traversal"
                    ],
                    "stall_points": [
                        {
                            "timestamp_range": "0:09 - 0:15",
                            "duration_minutes": 6,
                            "description": "Uncertainty regarding how to manage running prefix sums without recomputing paths",
                            "root_cause": "Hesitation in adapting standard array prefix patterns to tree recursive frames"
                        },
                        {
                            "timestamp_range": "0:23 - 0:27",
                            "duration_minutes": 4,
                            "description": "Submissions failed on branching paths due to contaminated hash map state",
                            "root_cause": "Omission of backtracking state restoration (decrementing count in hash map)"
                        }
                    ],
                    "behavioral_observations": [
                        "Proactively checks constraints (noticed negative numbers immediately)",
                        "Prone to state mutation leakage in recursive backtracking"
                    ]
                },
                "recommendations": {
                    "topics_to_strengthen": ["Tree DFS with State Rollback", "Prefix Sum Invariants"],
                    "behavioral_advice": "When writing backtracking DFS with shared collections (maps/sets), write the cleanup line immediately after the recursive call before filling in the rest.",
                    "similar_problems": ["Subarray Sum Equals K", "Path Sum IV", "Find Longest Awesome Substring"]
                }
            }
        },
        {
            "platform": "Codeforces",
            "problem_title": "1846E2 - Rudolf and Snowflakes (Hard Version)",
            "problem_statement": "Given n (1 <= n <= 10^18), determine if n can be represented as 1 + k + k^2 + ... + k^p for some integer k >= 2 and p >= 2. Hard version has n up to 10^18, while easy version had n <= 10^6.",
            "raw_notes": "0:00 - read problem. geometric progression sum: S = (k^(p+1) - 1)/(k - 1) == n with k>=2, p>=2.\n0:03 - for p=2: 1 + k + k^2 = n => k^2 + k + (1-n) = 0. We can solve quadratic for k in O(1) using integer square root.\n0:08 - for p >= 3: since k >= 2 and p >= 3, k^3 <= n <= 10^18, so k can at most be 10^6!\n0:12 - started implementing precomputation of all valid n for p >= 3 up to 10^18.\n0:17 - stuck: overflow issues with 64-bit integers when computing k^p for large powers.\n0:24 - spent 7 mins debugging __int128 vs uint64_t overflow bounds.\n0:29 - finished precomputing set for p >= 3 into unordered_set. For each query, if n in set return YES, else check if quadratic 1+k+k^2=n has integer root k >= 2.\n0:33 - submitted -> Accepted.",
            "solved": True,
            "time_taken_minutes": 33,
            "analysis": {
                "problem_analysis": {
                    "core_topics": ["Math / Number Theory", "Binary Search / Quadratic Equation", "Meet-in-the-middle / Bound Splitting"],
                    "difficulty_tier": "Hard (Codeforces 1700)",
                    "key_insight": "Decomposing into two cases based on power p: for p>=3 k is bounded by 10^6 (precomputable), for p=2 solve quadratic equation directly."
                },
                "thinking_analysis": {
                    "correct_moves": [
                        "Identified the bound asymmetry: p>=3 restricts k <= 10^6 drastically",
                        "Leveraged direct quadratic formula for p=2"
                    ],
                    "stall_points": [
                        {
                            "timestamp_range": "0:17 - 0:24",
                            "duration_minutes": 7,
                            "description": "Integer overflow during power multiplication while populating precomputation table",
                            "root_cause": "Improper overflow guards when multiplying 64-bit numbers near 10^18"
                        }
                    ],
                    "behavioral_observations": [
                        "Strong mathematical problem reduction skills",
                        "Struggles with defensive numeric limits and 64-bit integer overflow protection"
                    ]
                },
                "recommendations": {
                    "topics_to_strengthen": ["Safe Modular & Large Integer Arithmetic", "Overflow-free bounds checking"],
                    "behavioral_advice": "When computing products up to 10^18, use division bounds check (if k > LIMIT / current_term break) before multiplying.",
                    "similar_problems": ["CF 1850H - The Third Letter", "AtCoder ABC 230E - Fraction Floor Sum"]
                }
            }
        },
        {
            "platform": "AtCoder",
            "problem_title": "ABC 289E - Swap Places",
            "problem_statement": "Graph with N vertices and M edges. Takahashi starts at vertex 1, Aoki starts at vertex N. Each vertex has color 0 or 1. In one step, Takahashi and Aoki both move to adjacent vertices such that the colors of their destination vertices are different. Find minimum steps to reach swapped positions (Takahashi at N, Aoki at 1), or -1 if impossible. N, M <= 2000.",
            "raw_notes": "0:00 - read problem. Two people moving simultaneously on undirected graph. Vertex colors must differ at each step.\n0:03 - thought about bipartite matching or max flow? No, cost is minimum steps.\n0:07 - maybe BFS on Takahashi's graph and Aoki's graph separately?\n0:12 - tried writing separate BFS: find paths for Takahashi, then coordinate with Aoki. Got stuck realizing moves are synchronized and depend on each other's current vertex color.\n0:20 - gave up on separate BFS. Realized state space is joint (u, v) where u is Takahashi pos, v is Aoki pos.\n0:24 - worried about state space size: N=2000, so N^2 is 4 * 10^6. Is BFS on 4M states fast enough in 2 seconds?\n0:31 - implemented joint BFS with queue and 2D visited array dist[u][v].\n0:38 - TLE on test cases! Why? Because for vertex u with degree 2000 and vertex v with degree 2000, iterating all neighbors takes too long if total edges high.\n0:45 - ran out of contest time. Did not finish.",
            "solved": False,
            "time_taken_minutes": 45,
            "analysis": {
                "problem_analysis": {
                    "core_topics": ["Graph Theory", "Joint State BFS", "Complexity Estimation"],
                    "difficulty_tier": "Medium-Hard (AtCoder 1450)",
                    "key_insight": "Model the combined positions as vertices in a product graph (u, v) with up to 4*10^6 states, but optimize transition checking by grouping neighbors by color."
                },
                "thinking_analysis": {
                    "correct_moves": [
                        "Identified that the problem is minimum steps, pointing toward BFS over flow/matching",
                        "Correctly transitioned from flawed independent path search to joint product state (u, v)"
                    ],
                    "stall_points": [
                        {
                            "timestamp_range": "0:07 - 0:20",
                            "duration_minutes": 13,
                            "description": "Attempted to decouple synchronized movements into two separate single-agent searches",
                            "root_cause": "Reluctance to embrace higher-dimensional state space early"
                        },
                        {
                            "timestamp_range": "0:38 - 0:45",
                            "duration_minutes": 7,
                            "description": "Fell into TLE trap due to brute force iteration across all paired neighbors without color pruning",
                            "root_cause": "Inadequate transition optimization on dense bipartite-like neighbor scans"
                        }
                    ],
                    "behavioral_observations": [
                        "Fixates on decomposing inherently coupled state problems into decoupled heuristics",
                        "Slow to recognize and handle worst-case edge-to-vertex branching degree"
                    ]
                },
                "recommendations": {
                    "topics_to_strengthen": ["Product Graph BFS", "Transition Pruning by Equivalence Classes"],
                    "behavioral_advice": "When two entities move simultaneously, write the state as (A, B) immediately rather than spending 15 minutes attempting decoupled searches.",
                    "similar_problems": ["LeetCode 864 - Shortest Path to Get All Keys", "ABC 267F - Exactly K Steps"]
                }
            }
        }
    ]

    count = 0
    for s in samples:
        save_session(
            platform=s["platform"],
            problem_title=s["problem_title"],
            problem_statement=s["problem_statement"],
            raw_notes=s["raw_notes"],
            analysis_json=json.dumps(s["analysis"]),
            solved=s["solved"],
            time_taken_minutes=s["time_taken_minutes"],
            db_path=db_path,
        )
        count += 1
    return count
