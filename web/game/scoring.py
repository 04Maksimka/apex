"""Scoring logic for AstraGeek Sky Quiz."""

from typing import Optional

# ---------------------------------------------------------------------------
# Base points per difficulty
# ---------------------------------------------------------------------------
BASE_POINTS = {
    "easy": 100,
    "medium": 200,
    "hard": 350,
}

# ---------------------------------------------------------------------------
# Streak multipliers: streak_length -> multiplier
# ---------------------------------------------------------------------------
STREAK_MULTIPLIERS = [
    (10, 3.0),
    (5, 2.0),
    (3, 1.5),
    (2, 1.2),
    (0, 1.0),
]

# ---------------------------------------------------------------------------
# Time bonus: answer under N seconds gets +20 %
# ---------------------------------------------------------------------------
TIME_BONUS_SECONDS = 8
TIME_BONUS_MULTIPLIER = 1.2

# ---------------------------------------------------------------------------
# Hint penalty
# ---------------------------------------------------------------------------
HINT_MULTIPLIER = 0.5

# ---------------------------------------------------------------------------
# Rank thresholds (based on total score)
# ---------------------------------------------------------------------------
RANKS = [
    (5000, "🌌 Galactic Explorer"),
    (3000, "⭐ Star Navigator"),
    (1500, "🔭 Sky Watcher"),
    (500, "🌙 Night Apprentice"),
    (0, "🌑 Beginner"),
]


def _streak_multiplier(streak: int) -> float:
    for threshold, mult in STREAK_MULTIPLIERS:
        if streak >= threshold:
            return mult
    return 1.0


def calculate_score(
    difficulty: str,
    correct: bool,
    streak: int,
    used_hint: bool = False,
    time_seconds: Optional[float] = None,
    time_bonus_threshold: int = TIME_BONUS_SECONDS,  # ← добавить параметр
) -> int:
    """
    Calculate points awarded for a single answer.

    :param difficulty: 'easy' | 'medium' | 'hard'
    :type difficulty: str
    :param correct: whether the answer was correct
    :type correct: bool
    :param streak: current streak count (before this answer is counted)
    :type streak: int
    :param used_hint: whether the player used a hint
    :type used_hint: bool
    :param time_seconds: how long the player took to answer
    :type time_seconds: float
    :param time_bonus_threshold: how many seconds should the player bonus
    :type time_bonus_threshold: int
    :return: points awarded (0 for wrong answers)
    :rtype: int
    """
    if not correct:
        return 0

    base = BASE_POINTS.get(difficulty, 100)

    # Hint penalty
    if used_hint:
        base = int(base * HINT_MULTIPLIER)

    # Streak multiplier
    multiplier = _streak_multiplier(streak)

    # Time bonus
    if time_seconds is not None and time_seconds <= time_bonus_threshold:
        multiplier *= TIME_BONUS_MULTIPLIER

    return int(base * multiplier)


def get_rank(total_score: int) -> str:
    """Return the player rank label based on total score."""
    for threshold, label in RANKS:
        if total_score >= threshold:
            return label
    return RANKS[-1][1]


def build_result(
    session,
    correct: bool,
    correct_answer: str,
    player_answer: str,
    points: int,
    fun_fact: str,
) -> dict:
    """Build the result payload returned after each answer."""
    return {
        "correct": correct,
        "correct_answer": correct_answer,
        "player_answer": player_answer,
        "points_earned": points,
        "total_score": session.score,
        "streak": session.streak,
        "best_streak": session.best_streak,
        "round": session.round,
        "total_rounds": session.total_rounds,
        "accuracy": session.accuracy,
        "fun_fact": fun_fact,
        "is_finished": session.is_finished,
        "rank": get_rank(session.score),
    }
