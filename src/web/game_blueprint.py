"""
Flask Blueprint: /game/*
Provides REST API and page routing for AstraGeek Sky Quiz.

Registration in app.py:
    from src.web.game_blueprint import game_bp
    app.register_blueprint(game_bp)

Supported game modes
--------------------
constellation  — угадай созвездие по изображению (4 варианта)
star           — угадай название звезды по изображению (easy/medium/hard)
messier        — угадай номер объекта Мессье по pinhole-проекции
draw           — нарисуй контур созвездия по точкам-звёздам
trivia         — вопрос из базы фактов об астрономии (4 варианта)

URL-схема страниц
-----------------
GET /game/             →  лобби (games.html)
GET /game/lobby        →  лобби (games.html)
GET /game/<mode>       →  страница игры (game_<mode>.html или messier.html)

URL-схема API
-------------
POST /game/api/start       — создать сессию
GET  /game/api/question    — получить вопрос
POST /game/api/answer      — отправить ответ
GET  /game/api/hint        — получить подсказку
GET  /game/api/score       — текущий счёт сессии
POST /game/api/finish      — явно завершить сессию
GET  /game/api/modes       — список доступных режимов (мета-информация)
"""

from __future__ import annotations

import os
import threading
from typing import Any, Dict

from flask import Blueprint, abort, jsonify, request, send_from_directory

from src.game.question_factory import QuestionFactory
from src.game.scoring import build_result, calculate_score, get_rank
from src.game.session import (
    cleanup_old_sessions,
    create_session,
    delete_session,
    get_session,
)

game_bp = Blueprint("game", __name__, url_prefix="/game")
_factory = QuestionFactory()

VALID_MODES = {"constellation", "star", "messier", "draw", "trivia"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

# ---------------------------------------------------------------------------
# Static dir
# ---------------------------------------------------------------------------
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "public_html")

# ---------------------------------------------------------------------------
# Мета-информация о режимах (используется /game/api/modes и лобби)
# ---------------------------------------------------------------------------
MODES_META = [
    {
        "id": "constellation",
        "title": "Созвездия",
        "icon": "🌟",
        "description": "Угадай созвездие по участку карты неба. "
        "4 варианта ответа.",
        "tags": ["Карта неба", "4 варианта"],
    },
    {
        "id": "star",
        "title": "Звёзды",
        "icon": "⭐",
        "description": "Угадай название яркой звезды по изображению "
        "неба вокруг неё.",
        "tags": ["Яркие звёзды", "4 варианта / ввод"],
    },
    {
        "id": "messier",
        "title": "Объекты Мессье",
        "icon": "🌌",
        "description": "Угадай номер объекта каталога Мессье (M1–M110) "
        "по pinhole-проекции.",
        "tags": ["M1–M110", "Ввод числа"],
    },
    {
        "id": "draw",
        "title": "Нарисуй созвездие",
        "icon": "✏️",
        "description": "Соедини звёзды линиями так, чтобы получился "
        "правильный контур созвездия.",
        "tags": ["Рисование", "Память"],
    },
    {
        "id": "trivia",
        "title": "Астро-trivia",
        "icon": "🔭",
        "description": "Ответь на вопросы о физике, "
        "истории и мифологии астрономии.",
        "tags": ["Мифология", "Факты", "4 варианта"],
    },
]


# ---------------------------------------------------------------------------
# Static page routes
# ---------------------------------------------------------------------------


@game_bp.route("/")
@game_bp.route("/lobby")
def lobby():
    """Lobby. All available game modes."""
    return send_from_directory(_STATIC_DIR, "games.html")


@game_bp.route("/<mode>")
def game_page(mode: str):
    """
    Certain game page.
    For messier mode using messier.html.
    For all other  — game_<mode>.html.
    """
    if mode not in VALID_MODES:
        abort(404)

    filename = f"game_{mode}.html"

    path = os.path.join(_STATIC_DIR, filename)
    if not os.path.exists(path):
        abort(404)

    return send_from_directory(_STATIC_DIR, filename)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _err(msg: str, status: int = 400):
    return jsonify({"error": msg}), status


def _generate_question(session):
    """Dispatch to the correct question factory method."""
    mode = session.mode
    if mode == "constellation":
        return _factory.make_constellation_question(session)
    elif mode == "star":
        return _factory.make_star_question(session)
    elif mode == "messier":
        return _factory.make_messier_question(session)
    elif mode == "draw":
        return _factory.make_draw_question(session)
    elif mode == "trivia":
        return _factory.make_trivia_question(session)
    else:
        raise ValueError(f"Unknown mode: {mode}")


# ---------------------------------------------------------------------------
# Prefetch logic — background pre-generation of next question
# ---------------------------------------------------------------------------


def _prefetch_worker(session) -> None:
    """
    Runs in a daemon thread. Generates the next question and stores it in
    session.current_question.
    Sets session.prefetch_event when done (or on error).
    """
    try:
        if session.is_finished:
            # Nothing to prefetch — just signal so api_question doesn't hang.
            return
        _generate_question(session)
        # _generate_question sets session.current_question as a side-effect.
    except Exception as exc:
        session.prefetch_error = str(exc)
    finally:
        session.prefetch_event.set()


def _schedule_prefetch(session) -> None:
    """
    Reset prefetch state and launch a daemon thread to pre-generate
    the next question image.

    Call this:
      • right after create_session() in api_start
      • right after scoring in api_answer (before returning the result)
    """
    session.prefetch_event.clear()
    session.prefetch_error = None
    t = threading.Thread(target=_prefetch_worker, args=(session,), daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Meta endpoint
# ---------------------------------------------------------------------------


@game_bp.route("/api/modes", methods=["GET"])
def api_modes():
    """
    GET /game/api/modes
    Returns all available game modes with description.
    """
    return jsonify(MODES_META)


# ---------------------------------------------------------------------------
# Game session endpoints
# ---------------------------------------------------------------------------


@game_bp.route("/api/start", methods=["POST"])
def api_start():
    """
    POST /game/api/start
    Body:
        { "mode": "constellation", "difficulty": "easy", "rounds": 10 }
    Answer:
        { "session_id": "...", "mode": ...,
        "difficulty": ..., "total_rounds": ... }
    """
    cleanup_old_sessions()
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

    mode = data.get("mode", "constellation")
    difficulty = data.get("difficulty", "easy")
    rounds = int(data.get("rounds", 10))

    if mode not in VALID_MODES:
        return _err(f"Invalid mode. Choose from: {sorted(VALID_MODES)}")
    if difficulty not in VALID_DIFFICULTIES:
        return _err("Invalid difficulty. Choose from: easy, medium, hard")
    if not (1 <= rounds <= 30):
        return _err("rounds must be between 1 and 30")

    session = create_session(
        mode=mode, difficulty=difficulty, total_rounds=rounds
    )

    # ── Start generating the first question in the background ─────────────
    # By the time the browser renders the UI and calls /api/question,
    # the image will already be ready (or almost ready).

    _schedule_prefetch(session)

    return jsonify(session.to_dict()), 201


@game_bp.route("/api/question", methods=["GET"])
def api_question():
    """
    GET /game/api/question?session_id=<id>
    Returns the next question for the current session.

    If background generation (started by api_start or api_answer) has not
    finished yet — waits up to 90 seconds. If nothing happens within that
    time or an error occurs — generates synchronously as a fallback.

    NOTE: correct_ra_deg / correct_dec_deg are intentionally NOT forwarded
    to the client — they are stored in session.current_question only for
    server-side answer validation.
    """

    session_id = request.args.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return _err("Session not found", 404)

    if session.is_finished:
        return jsonify(
            {
                "finished": True,
                **session.to_dict(),
                "rank": get_rank(session.score),
            }
        )

    # ── Waiting for background (max 90 s) ────────────────────────
    prefetch_ready = session.prefetch_event.wait(timeout=90.0)

    if (
        prefetch_ready
        and not session.prefetch_error
        and session.current_question is not None
    ):
        # If already generated -- use it
        question = session.current_question
    else:
        # Sync generating
        if session.prefetch_error:
            print(
                f"[prefetch] Ошибка предгенерации для {session.session_id}: "
                f"{session.prefetch_error} — генерируем синхронно"
            )
            session.prefetch_error = None
        try:
            question = _generate_question(session)
        except Exception as exc:
            return _err(f"Failed to generate question: {exc}", 500)

    resp = {
        "session": session.to_dict(),
        "question_type": question["type"],
        "question": question["question"],
        "hint": question.get("hint", ""),
        "round": session.round + 1,
    }

    if question["type"] == "draw":
        resp["stars"] = question["stars"]
    else:
        resp["image"] = question["image"]
        resp["options"] = question["options"]

    return jsonify(resp)


@game_bp.route("/api/answer", methods=["POST"])
def api_answer():
    """
    POST /game/api/answer

    Normal modes body:
        { "session_id": "...", "answer": "Orion",
         "used_hint": false, "time_seconds": 7 }

    Star hard mode extra fields:
        { ..., "answer_ra": 101.3, "answer_dec": -16.7 }

    Draw mode body:
        { "session_id": "...", "drawn_edges": [[hip1,hip2],...],
        "used_hint": false, "time_seconds": 30 }
    """
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    if not session.current_question:
        return _err("No active question; call /api/question first")

    used_hint = bool(data.get("used_hint", False))
    time_seconds = data.get("time_seconds")

    coord_feedback = None
    draw_details = None

    # ── Draw mode ────────────────────────────────────────────────────────────
    if session.current_question["type"] == "draw":
        drawn_edges = data.get("drawn_edges", [])
        result = _factory.check_draw_answer(session, drawn_edges)
        correct = result.get("correct", False)
        correct_answer = result.get("correct_answer", "")
        player_answer = f"{result.get('score_pct', 0):.0f}% линий совпало"
        fun_fact = result.get("fun_fact", "")
        draw_details = result

    # ── All other modes ──────────────────────────────────────────────────────
    else:
        player_answer = str(data.get("answer", "")).strip()
        correct_answer = session.current_question.get("correct", "")
        fun_fact = session.current_question.get("fun_fact", "")
        name_correct = player_answer.lower() == correct_answer.lower()

        # Star hard-mode: also validate equatorial coordinates (±10°)
        if (
            session.current_question.get("type") == "star"
            and session.difficulty == "hard"
        ):
            correct_ra = session.current_question.get("correct_ra_deg")
            correct_dec = session.current_question.get("correct_dec_deg")

            if correct_ra is not None and correct_dec is not None:
                try:
                    answer_ra = float(data["answer_ra"])
                    answer_dec = float(data["answer_dec"])
                    # RA is circular (0–360°) — use shortest arc
                    ra_diff = abs(((answer_ra - correct_ra + 180) % 360) - 180)
                    dec_diff = abs(answer_dec - correct_dec)
                    ra_ok = ra_diff <= 10.0
                    dec_ok = dec_diff <= 10.0
                    correct = name_correct and ra_ok and dec_ok
                    coord_feedback = {
                        "ra_ok": ra_ok,
                        "dec_ok": dec_ok,
                        "user_ra": round(answer_ra, 1),
                        "user_dec": round(answer_dec, 1),
                        "correct_ra": round(correct_ra, 1),
                        "correct_dec": round(correct_dec, 1),
                        "ra_diff": round(ra_diff, 1),
                        "dec_diff": round(dec_diff, 1),
                    }
                except (KeyError, TypeError, ValueError):
                    # Coordinates not provided or invalid — mark only name
                    correct = name_correct
            else:
                correct = name_correct
        else:
            correct = name_correct

    # ── Scoring ──────────────────────────────────────────────────────────────
    points = calculate_score(
        difficulty=session.difficulty,
        correct=correct,
        streak=session.streak,
        used_hint=used_hint,
        time_seconds=float(time_seconds) if time_seconds is not None else None,
    )
    session.score += points
    session.round += 1
    if correct:
        session.streak += 1
        session.correct_count += 1
        session.best_streak = max(session.best_streak, session.streak)
    else:
        session.streak = 0

    session.history.append(
        {
            "round": session.round,
            "correct": correct,
            "points": points,
            "answer": player_answer,
        }
    )
    session.current_question = None  # before prefetch

    # ── Pregenerating next question ──────────────
    # Be the time the user reads the result and click Next, the image will be
    # ready in session.current_question.

    if not session.is_finished:
        _schedule_prefetch(session)

    resp = build_result(
        session=session,
        correct=correct,
        correct_answer=correct_answer,
        player_answer=player_answer,
        points=points,
        fun_fact=fun_fact,
    )

    if draw_details is not None:
        resp["draw_details"] = draw_details
    if coord_feedback is not None:
        resp["coord_feedback"] = coord_feedback
        resp["name_correct"] = name_correct

    return jsonify(resp)


@game_bp.route("/api/hint", methods=["GET"])
def api_hint():
    """
    GET /game/api/hint?session_id=<id>
    Returns the hint for the current question.
    Using a hint reduces the score multiplier by 50%.

    Answer: { "hint": "Это созвездие зимнего неба..." }
    """
    session_id = request.args.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    if not session.current_question:
        return _err("No active question")
    return jsonify({"hint": session.current_question.get("hint", "")})


@game_bp.route("/api/score", methods=["GET"])
def api_score():
    """
    GET /game/api/score?session_id=<id>
    Returns score and statistics
    """
    session_id = request.args.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    return jsonify({**session.to_dict(), "rank": get_rank(session.score)})


@game_bp.route("/api/finish", methods=["POST"])
def api_finish():
    """
    POST /game/api/finish
    Explicitly ends the session and returns the final statistics.
    After the call, the session_id becomes invalid.
    """
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "")
    session = get_session(session_id)
    if not session:
        return _err("Session not found", 404)

    result = {
        **session.to_dict(),
        "rank": get_rank(session.score),
        "history": session.history,
    }
    delete_session(session_id)
    return jsonify(result)
