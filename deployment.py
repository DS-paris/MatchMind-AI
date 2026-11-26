"""Small, fail-closed controls for a single-process public portfolio deployment.

Stores request counts only: never questions, keys, IPs or resume text.
"""
from contextlib import contextmanager
import hashlib
import hmac
from pathlib import Path
import sqlite3
from threading import BoundedSemaphore
import time


class AccessDenied(ValueError):
    pass


def public_mode(value="true"):
    return str(value).lower() not in {"false", "0", "no"}


def authorized(expected, supplied):
    # Short/missing server secrets deliberately leave paid features locked.
    return len(expected) >= 24 and hmac.compare_digest(
        hashlib.sha256(expected.encode()).digest(), hashlib.sha256(supplied.encode()).digest())


class AgentBudget:
    """Atomic rolling quotas on one host; failed attempts consume quota too."""
    def __init__(self, path, daily=30, hourly=5, cooldown=15):
        self.path = Path(path)
        self.daily, self.hourly, self.cooldown = daily, hourly, cooldown
        self.slot = BoundedSemaphore(1)

    def reserve(self, session_id, now=None):
        now = time.time() if now is None else now
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute("CREATE TABLE IF NOT EXISTS attempts (session TEXT NOT NULL, ts REAL NOT NULL)")
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM attempts WHERE ts <= ?", (now - 86400,))
            total = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            recent, latest = db.execute(
                "SELECT COUNT(*), MAX(ts) FROM attempts WHERE session = ? AND ts > ?",
                (session_id, now - 3600)).fetchone()
            if total >= self.daily or recent >= self.hourly:
                raise AccessDenied("Assistant request allowance reached. Local search remains available.")
            if latest is not None and now - latest < self.cooldown:
                raise AccessDenied("Please wait before asking another assistant question.")
            db.execute("INSERT INTO attempts VALUES (?, ?)", (session_id, now))

    @contextmanager
    def request(self, session_id):
        if not self.slot.acquire(blocking=False):
            raise AccessDenied("The assistant is busy. Please try again shortly.")
        try:
            self.reserve(session_id)
            yield
        finally:
            self.slot.release()


# Module lifetime, not st.session_state: clearing a workspace cannot reset quotas.
AGENT_BUDGET = AgentBudget(Path(__file__).parent / ".cache" / "agent_budget.sqlite3")
INDEX_SLOT = BoundedSemaphore(1)


@contextmanager
def indexing_slot():
    if not INDEX_SLOT.acquire(blocking=False):
        raise AccessDenied("Another index is being built. Please try again shortly.")
    try:
        yield
    finally:
        INDEX_SLOT.release()
