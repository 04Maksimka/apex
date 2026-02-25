"""In-memory game session management for AstraGeek Sky Quiz."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# In-memory store (replace with Redis / SQLite for production)
# ---------------------------------------------------------------------------
_sessions: Dict[str, "GameSession"] = {}


# ---------------------------------------------------------------------------
# Difficulty configuration
# ---------------------------------------------------------------------------
DIFFICULTY_CONSTELLATIONS: Dict[str, Optional[List[str]]] = {
    "easy": [
        "ORI",
        "UMA",
        "CAS",
        "CYG",
        "LEO",
        "SCO",
        "GEM",
        "TAU",
        "AQL",
        "LYR",
        "PER",
        "AUR",
        "VIR",
        "SGR",
        "AND",
    ],
    "medium": [
        "ORI",
        "UMA",
        "CAS",
        "CYG",
        "LEO",
        "SCO",
        "GEM",
        "TAU",
        "AQL",
        "LYR",
        "PER",
        "AUR",
        "VIR",
        "SGR",
        "AND",
        "BOO",
        "HER",
        "AQR",
        "CAP",
        "PSC",
        "ARI",
        "CNC",
        "CMI",
        "CMA",
        "CRU",
        "GRU",
        "COR",
        "UMI",
        "DRA",
        "CEP",
        "CET",
        "ERI",
        "PEG",
        "DEL",
        "SAG",
        "OPH",
        "SER",
    ],
    "hard": None,  # All available constellations
}

DIFFICULTY_MAGNITUDE: Dict[str, float] = {
    "easy": 5.0,
    "medium": 5.5,
    "hard": 6.0,
}

TOTAL_ROUNDS_DEFAULT = 10


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------
@dataclass
class GameSession:
    session_id: str
    mode: str  # constellation | star | messier | draw | trivia
    difficulty: str  # easy | medium | hard

    score: int = 0
    round: int = 0
    total_rounds: int = TOTAL_ROUNDS_DEFAULT
    streak: int = 0
    best_streak: int = 0
    correct_count: int = 0

    used_objects: Set[Any] = field(default_factory=set)
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_question: Optional[Dict[str, Any]] = None

    @property
    def is_finished(self) -> bool:
        return self.round >= self.total_rounds

    @property
    def accuracy(self) -> float:
        if self.round == 0:
            return 0.0
        return round(self.correct_count / self.round * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "score": self.score,
            "round": self.round,
            "total_rounds": self.total_rounds,
            "streak": self.streak,
            "best_streak": self.best_streak,
            "correct_count": self.correct_count,
            "accuracy": self.accuracy,
            "is_finished": self.is_finished,
        }


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------
def create_session(
    mode: str, difficulty: str, total_rounds: int = TOTAL_ROUNDS_DEFAULT
) -> GameSession:
    session_id = str(uuid.uuid4())
    session = GameSession(
        session_id=session_id,
        mode=mode,
        difficulty=difficulty,
        total_rounds=total_rounds,
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[GameSession]:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def cleanup_old_sessions(max_sessions: int = 1000) -> None:
    """Remove oldest sessions if the store gets too large."""
    if len(_sessions) > max_sessions:
        oldest_keys = list(_sessions.keys())[: len(_sessions) - max_sessions]
        for k in oldest_keys:
            del _sessions[k]
