from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class GitRepositoryError(RuntimeError):
    """Raised when Git repository information cannot be retrieved."""


@dataclass(slots=True)
class GitRevisionStatus:
    branch: str
    local_commit: str
    remote_commit: str
    commits_behind: int
    checked_at: datetime


class GitRepositoryTracker:
    """Thin wrapper over git CLI to detect local vs remote revisions."""

    def __init__(
        self,
        *,
        repo_path: Path,
        remote: str = "origin",
        branch: str = "main",
        auto_fetch: bool = True,
    ) -> None:
        self._repo_path = repo_path
        self._remote = remote
        self._branch = branch
        self._auto_fetch = auto_fetch

    @property
    def repo_path(self) -> Path:
        return self._repo_path

    @property
    def branch(self) -> str:
        return self._branch

    @property
    def remote_ref(self) -> str:
        return f"{self._remote}/{self._branch}"

    def is_available(self) -> bool:
        return (self._repo_path / ".git").exists()

    def check_status(self) -> GitRevisionStatus:
        if not self.is_available():
            raise GitRepositoryError(f"Git repository not found at {self._repo_path}")

        if self._auto_fetch:
            self._run_git("fetch", "--prune", self._remote, self._branch)

        local_commit = self._run_git("rev-parse", "HEAD")
        remote_commit = self._run_git("rev-parse", self.remote_ref)
        behind_raw = self._run_git("rev-list", "--count", f"{local_commit}..{self.remote_ref}")
        commits_behind = int(behind_raw or "0")

        return GitRevisionStatus(
            branch=self._branch,
            local_commit=local_commit,
            remote_commit=remote_commit,
            commits_behind=max(commits_behind, 0),
            checked_at=datetime.now(timezone.utc),
        )

    def _run_git(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitRepositoryError("git executable is not available") from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise GitRepositoryError(f"git {' '.join(args)} failed: {stderr or 'unknown error'}")
        return result.stdout.strip()


__all__ = [
    "GitRepositoryError",
    "GitRepositoryTracker",
    "GitRevisionStatus",
]
