"""Background Queue Manager — run pipeline jobs asynchronously with state tracking.

Queue state is persisted in .queue_state.json in the projects directory.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUEUE_STATE_FILE = ".queue_state.json"

_JOB_STATUS_PENDING = "pending"
_JOB_STATUS_RUNNING = "running"
_JOB_STATUS_COMPLETED = "completed"
_JOB_STATUS_FAILED = "failed"
_JOB_STATUS_CANCELLED = "cancelled"


class QueueManager:
    def __init__(self, projects_dir: str | Path):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self) -> Path:
        return self.projects_dir / QUEUE_STATE_FILE

    def load_state(self) -> dict[str, Any]:
        path = self._state_path()
        if path.exists():
            return json.loads(path.read_text())
        return {"jobs": [], "next_id": 1}

    def save_state(self, state: dict[str, Any]) -> None:
        path = self._state_path()
        path.write_text(json.dumps(state, indent=2) + "\n")

    def add_job(self, case_id: str, mode: str = "production", dry_run: bool = False) -> int:
        state = self.load_state()
        job_id = state["next_id"]
        state["next_id"] += 1

        job = {
            "id": job_id,
            "case_id": case_id,
            "mode": mode,
            "dry_run": dry_run,
            "status": _JOB_STATUS_PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "pid": None,
            "log_file": None,
        }
        state["jobs"].append(job)
        self.save_state(state)
        return job_id

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        state = self.load_state()
        for job in state["jobs"]:
            if job["id"] == job_id:
                return job
        return None

    def update_job(self, job_id: int, **kwargs) -> None:
        state = self.load_state()
        for job in state["jobs"]:
            if job["id"] == job_id:
                job.update(kwargs)
                break
        self.save_state(state)

    def list_jobs(self, status: str | None = None) -> list[dict[str, Any]]:
        state = self.load_state()
        jobs = state["jobs"]
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        return jobs

    def start_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if not job or job["status"] != _JOB_STATUS_PENDING:
            return False

        case_id = job["case_id"]
        mode = job["mode"]
        dry_run = job["dry_run"]

        log_dir = self.projects_dir / case_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"queue_job_{job_id}.log"

        cmd = [
            sys.executable, "-m", "shadow_protocol.cli", case_id,
            "--mode", mode,
        ]
        if dry_run:
            cmd.append("--dry-run")

        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            cwd=self.projects_dir.parent,
        )

        self.update_job(
            job_id,
            status=_JOB_STATUS_RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
            pid=proc.pid,
            log_file=str(log_file),
        )
        return True

    def poll_job(self, job_id: int) -> dict[str, Any] | None:
        job = self.get_job(job_id)
        if not job or job["status"] != _JOB_STATUS_RUNNING:
            return job

        pid = job.get("pid")
        if pid is None:
            return job

        try:
            pid_int = int(pid)
        except (ValueError, TypeError):
            return job

        try:
            os.kill(pid_int, 0)
        except OSError:
            log_file = job.get("log_file")
            if log_file and Path(log_file).exists():
                log_content = Path(log_file).read_text()
                if "Pipeline complete" in log_content:
                    self.update_job(job_id, status=_JOB_STATUS_COMPLETED, finished_at=datetime.now(timezone.utc).isoformat(), exit_code=0)
                else:
                    self.update_job(job_id, status=_JOB_STATUS_FAILED, finished_at=datetime.now(timezone.utc).isoformat(), exit_code=1)
            else:
                self.update_job(job_id, status=_JOB_STATUS_FAILED, finished_at=datetime.now(timezone.utc).isoformat(), exit_code=1)

        return self.get_job(job_id)

    def poll_all(self) -> list[dict[str, Any]]:
        running = self.list_jobs(status=_JOB_STATUS_RUNNING)
        for job in running:
            self.poll_job(job["id"])
        return self.list_jobs()

    def cancel_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if not job or job["status"] not in (_JOB_STATUS_PENDING, _JOB_STATUS_RUNNING):
            return False

        if job["status"] == _JOB_STATUS_RUNNING:
            pid = job.get("pid")
            if pid is not None:
                try:
                    os.kill(int(pid), 15)
                except (OSError, ValueError):
                    pass

        self.update_job(job_id, status=_JOB_STATUS_CANCELLED, finished_at=datetime.now(timezone.utc).isoformat())
        return True
