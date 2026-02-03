"""
SQLite-based persistence for workflow state.

Tracks workflow runs, step executions, and assets with versioning.
Enables resume capability for failed/interrupted workflows.
"""

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional


class PersistenceLayer:
    """SQLite-based persistence for workflow state."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".localforge" / "runs.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    recipe_path TEXT NOT NULL,
                    recipe_name TEXT,
                    status TEXT DEFAULT 'pending',
                    inputs TEXT DEFAULT '{}',
                    outputs TEXT DEFAULT '{}',
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    run_directory TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS step_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_name TEXT,
                    status TEXT DEFAULT 'pending',
                    inputs TEXT DEFAULT '{}',
                    outputs TEXT DEFAULT '{}',
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES workflow_runs(id),
                    UNIQUE(run_id, step_id)
                );

                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    run_id TEXT,
                    asset_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    file_size INTEGER,
                    metadata TEXT DEFAULT '{}',
                    tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (run_id) REFERENCES workflow_runs(id)
                );

                CREATE TABLE IF NOT EXISTS asset_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(id),
                    UNIQUE(asset_id, version)
                );

                CREATE INDEX IF NOT EXISTS idx_runs_project ON workflow_runs(project_id);
                CREATE INDEX IF NOT EXISTS idx_runs_status ON workflow_runs(status);
                CREATE INDEX IF NOT EXISTS idx_steps_run ON step_executions(run_id);
                CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id);
                CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
            """)

    @contextmanager
    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ==================== Run Management ====================

    def start_run(self, recipe_path: str, inputs: Dict, project_id: str = None,
                  run_directory: str = None) -> str:
        run_id = str(uuid.uuid4())[:8]
        recipe_name = Path(recipe_path).stem

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO workflow_runs
                   (id, project_id, recipe_path, recipe_name, status, inputs,
                    started_at, run_directory)
                   VALUES (?, ?, ?, ?, 'running', ?, CURRENT_TIMESTAMP, ?)""",
                (run_id, project_id, recipe_path, recipe_name,
                 json.dumps(inputs), run_directory),
            )
            if project_id:
                conn.execute(
                    "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (project_id,),
                )
        return run_id

    def complete_run(self, run_id: str, outputs: Dict, status: str = "completed"):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE workflow_runs
                   SET status = ?, outputs = ?, completed_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (status, json.dumps(outputs, default=str), run_id),
            )

    def fail_run(self, run_id: str, error_message: str):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE workflow_runs
                   SET status = 'failed', error_message = ?,
                       completed_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (error_message, run_id),
            )

    def get_run(self, run_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result["inputs"] = json.loads(result["inputs"])
                result["outputs"] = json.loads(result["outputs"])
                return result
        return None

    def list_runs(self, project_id: str = None, status: str = None,
                  limit: int = 50) -> List[Dict]:
        query = "SELECT * FROM workflow_runs WHERE 1=1"
        params: list = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["inputs"] = json.loads(result["inputs"])
                result["outputs"] = json.loads(result["outputs"])
                results.append(result)
            return results

    # ==================== Step Tracking ====================

    def start_step(self, run_id: str, step_id: str, step_name: str, inputs: Dict):
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO step_executions
                   (run_id, step_id, step_name, status, inputs, started_at)
                   VALUES (?, ?, ?, 'running', ?, CURRENT_TIMESTAMP)""",
                (run_id, step_id, step_name, json.dumps(inputs, default=str)),
            )

    def complete_step(self, run_id: str, step_id: str, outputs: Dict):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE step_executions
                   SET status = 'completed', outputs = ?,
                       completed_at = CURRENT_TIMESTAMP
                   WHERE run_id = ? AND step_id = ?""",
                (json.dumps(outputs, default=str), run_id, step_id),
            )

    def fail_step(self, run_id: str, step_id: str, error_message: str):
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE step_executions
                   SET status = 'failed', error_message = ?,
                       completed_at = CURRENT_TIMESTAMP
                   WHERE run_id = ? AND step_id = ?""",
                (error_message, run_id, step_id),
            )

    def get_completed_steps(self, run_id: str) -> Dict[str, Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT step_id, outputs FROM step_executions
                   WHERE run_id = ? AND status = 'completed'""",
                (run_id,),
            ).fetchall()
            return {row["step_id"]: json.loads(row["outputs"]) for row in rows}

    # ==================== Asset Management ====================

    def register_asset(self, file_path: str, asset_type: str, name: str = None,
                       project_id: str = None, run_id: str = None,
                       metadata: Dict = None, tags: List[str] = None) -> str:
        asset_id = str(uuid.uuid4())[:8]
        fp = Path(file_path)
        name = name or fp.stem
        file_hash = self._hash_file(fp) if fp.exists() else None
        file_size = fp.stat().st_size if fp.exists() else None

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO assets
                   (id, project_id, run_id, asset_type, name, file_path,
                    file_hash, file_size, metadata, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (asset_id, project_id, run_id, asset_type, name, str(fp),
                 file_hash, file_size, json.dumps(metadata or {}),
                 json.dumps(tags or [])),
            )
            conn.execute(
                """INSERT INTO asset_versions (asset_id, version, file_path, file_hash)
                   VALUES (?, 1, ?, ?)""",
                (asset_id, str(fp), file_hash),
            )
        return asset_id

    def get_stats(self, project_id: str = None) -> Dict:
        with self._get_conn() as conn:
            base = "WHERE project_id = ?" if project_id else "WHERE 1=1"
            params = [project_id] if project_id else []

            run_stats = conn.execute(
                f"""SELECT COUNT(*) as total,
                    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
                    FROM workflow_runs {base}""",
                params,
            ).fetchone()

            return {"runs": dict(run_stats)}

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]


_persistence: Optional[PersistenceLayer] = None


def get_persistence(db_path: str = None) -> PersistenceLayer:
    """Get or create persistence singleton."""
    global _persistence
    if _persistence is None:
        _persistence = PersistenceLayer(db_path)
    return _persistence
