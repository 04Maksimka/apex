"""
Flask Blueprint: /game/*
Provides REST API and page routing for AstraGeek Sky Quiz.

Registration in app.py:
    from src.web.game_blueprint import game_bp
    app.register_blueprint(game_bp)

Supported game modes
--------------------
constellation  — угадай созвездие по изображению (4 варианта)
star           — угадай название звезды по изображению (4 варианта)
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

import time
from typing import Any, Dict

from flask import Blueprint, jsonify, request, send_from_directory, abort
import os

from src.game.session import (
    create_session, get_session, delete_session, cleanup_old_sessions,
    DIFFICULTY_CONSTELLATIONS,
)
from src.game.question_factory import QuestionFactory
from src.game.scoring import calculate_score, get_rank, build_result

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
        "id":          "constellation",
        "title":       "Созвездия",
        "icon":        "🌟",
        "description": "Угадай созвездие по участку карты неба. 4 варианта ответа.",
        "tags":        ["Карта неба", "4 варианта"],
    },
    {
        "id":          "star",
        "title":       "Звёзды",
        "icon":        "⭐",
        "description": "Угадай название яркой звезды по изображению неба вокруг неё.",
        "tags":        ["Яркие звёзды", "4 варианта"],
    },
    {
        "id":          "messier",
        "title":       "Объекты Мессье",
        "icon":        "🌌",
        "description": "Угадай номер объекта каталога Мессье (M1–M110) по pinhole-проекции.",
        "tags":        ["M1–M110", "Ввод числа"],
    },
    {
        "id":          "draw",
        "title":       "Нарисуй созвездие",
        "icon":        "✏️",
        "description": "Соедини звёзды линиями так, чтобы получился правильный контур созвездия.",
        "tags":        ["Рисование", "Память"],
    },
    {
        "id":          "trivia",
        "title":       "Астро-триvia",
        "icon":        "🔭",
        "description": "Ответь на вопросы о физике, истории и мифологии астрономии.",
        "tags":        ["Мифология", "Факты", "4 варианта"],
    },
]


# ---------------------------------------------------------------------------
# Static page routes
# ---------------------------------------------------------------------------

@game_bp.route("/")
@game_bp.route("/lobby")
def lobby():
    """Лобби: список всех доступных игр."""
    return send_from_directory(_STATIC_DIR, "games.html")


@game_bp.route("/<mode>")
def game_page(mode: str):
    """
    Страница отдельной игры.
    Для режима messier используется messier.html (отдельный движок).
    Для остальных режимов — game_<mode>.html.
    """
    if mode not in VALID_MODES:
        abort(404)

    # Режим Мессье использует собственный файл страницы и API (/api/messier/*)
    if mode == "messier":
        filename = "messier.html"
    else:
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
# Meta endpoint
# ---------------------------------------------------------------------------

@game_bp.route("/api/modes", methods=["GET"])
def api_modes():
    """
    GET /game/api/modes
    Возвращает список доступных игровых режимов с описанием.
    Используется фронтендом лобби для динамического рендера карточек.
    """
    return jsonify(MODES_META)


# ---------------------------------------------------------------------------
# Game session endpoints
# ---------------------------------------------------------------------------

@game_bp.route("/api/start", methods=["POST"])
def api_start():
    """
    POST /game/api/start
    Тело запроса:
        { "mode": "constellation", "difficulty": "easy", "rounds": 10 }
    Ответ:
        { "session_id": "...", "mode": ..., "difficulty": ..., "total_rounds": ... }

    Параметры:
        mode        — игровой режим: constellation | star | messier | draw | trivia
        difficulty  — сложность: easy | medium | hard
        rounds      — количество раундов (1–30, по умолчанию 10)

    Примечание: режим messier управляется отдельным blueprint-ом (/api/messier/*).
    Этот эндпоинт создаёт сессию для остальных четырёх режимов.
    """
    cleanup_old_sessions()
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

    mode       = data.get("mode", "constellation")
    difficulty = data.get("difficulty", "easy")
    rounds     = int(data.get("rounds", 10))

    if mode not in VALID_MODES:
        return _err(f"Invalid mode. Choose from: {sorted(VALID_MODES)}")
    if difficulty not in VALID_DIFFICULTIES:
        return _err("Invalid difficulty. Choose from: easy, medium, hard")
    if not (1 <= rounds <= 30):
        return _err("rounds must be between 1 and 30")

    session = create_session(mode=mode, difficulty=difficulty, total_rounds=rounds)
    return jsonify(session.to_dict()), 201


@game_bp.route("/api/question", methods=["GET"])
def api_question():
    """
    GET /game/api/question?session_id=<id>
    Возвращает следующий вопрос текущей сессии.

    Ответ (общий):
        {
          "session":       { ...состояние сессии... },
          "question_type": "constellation" | "star" | "draw" | "trivia",
          "question":      "Какое это созвездие?",
          "hint":          "Подсказка (если доступна)",
          "round":         3
        }

    Дополнительные поля:
        Для draw-режима:  "stars": [{ "hip": int, "x": float, "y": float }, ...]
        Для остальных:    "image": "<base64>",  "options": ["A", "B", "C", "D"]

    Если сессия завершена, возвращает:
        { "finished": true, ...итоговые данные..., "rank": "⭐ Star Navigator" }
    """
    session_id = request.args.get("session_id", "")
    session    = get_session(session_id)
    if not session:
        return _err("Session not found", 404)

    if session.is_finished:
        return jsonify({
            "finished": True,
            **session.to_dict(),
            "rank": get_rank(session.score),
        })

    try:
        question = _generate_question(session)
    except Exception as exc:
        return _err(f"Failed to generate question: {exc}", 500)

    resp = {
        "session":       session.to_dict(),
        "question_type": question["type"],
        "question":      question["question"],
        "hint":          question.get("hint", ""),
        "round":         session.round + 1,
    }

    if question["type"] == "draw":
        resp["stars"]   = question["stars"]
    else:
        resp["image"]   = question["image"]
        resp["options"] = question["options"]

    return jsonify(resp)


@game_bp.route("/api/answer", methods=["POST"])
def api_answer():
    """
    POST /game/api/answer
    Принимает ответ игрока и возвращает результат раунда.

    Тело запроса (обычные режимы):
        {
          "session_id":  "...",
          "answer":      "Orion",
          "used_hint":   false,
          "time_seconds": 7
        }

    Тело запроса (draw-режим):
        {
          "session_id":   "...",
          "drawn_edges":  [[hip1, hip2], [hip2, hip3], ...],
          "used_hint":    false,
          "time_seconds": 30
        }

    Ответ:
        {
          "correct":        true,
          "correct_answer": "Orion",
          "player_answer":  "Orion",
          "points":         240,
          "score":          840,
          "streak":         3,
          "fun_fact":       "Ригель — голубой сверхгигант...",
          "round":          3,
          "total_rounds":   10,
          "finished":       false
        }
    """
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "")
    session    = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    if not session.current_question:
        return _err("No active question; call /api/question first")

    used_hint    = bool(data.get("used_hint", False))
    time_seconds = data.get("time_seconds")

    # Draw mode has its own evaluation
    if session.current_question["type"] == "draw":
        drawn_edges    = data.get("drawn_edges", [])
        result         = _factory.check_draw_answer(session, drawn_edges)
        correct        = result.get("correct", False)
        correct_answer = result.get("correct_answer", "")
        player_answer  = f"{result.get('score_pct', 0):.0f}% линий совпало"
        fun_fact       = result.get("fun_fact", "")
    else:
        player_answer  = str(data.get("answer", "")).strip()
        correct_answer = session.current_question.get("correct", "")
        correct        = player_answer.lower() == correct_answer.lower()
        fun_fact       = session.current_question.get("fun_fact", "")

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
        session.streak      += 1
        session.correct_count += 1
        session.best_streak  = max(session.best_streak, session.streak)
    else:
        session.streak = 0

    session.history.append({
        "round":   session.round,
        "correct": correct,
        "points":  points,
        "answer":  player_answer,
    })
    session.current_question = None

    resp = build_result(
        session=session,
        correct=correct,
        correct_answer=correct_answer,
        player_answer=player_answer,
        points=points,
        fun_fact=fun_fact,
    )
    if session.current_question and session.current_question.get("type") == "draw":
        resp["draw_details"] = result

    return jsonify(resp)


@game_bp.route("/api/hint", methods=["GET"])
def api_hint():
    """
    GET /game/api/hint?session_id=<id>
    Возвращает подсказку к текущему вопросу.
    Использование подсказки снижает множитель очков на 50%.

    Ответ: { "hint": "Это созвездие зимнего неба..." }
    """
    session_id = request.args.get("session_id", "")
    session    = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    if not session.current_question:
        return _err("No active question")
    return jsonify({"hint": session.current_question.get("hint", "")})


@game_bp.route("/api/score", methods=["GET"])
def api_score():
    """
    GET /game/api/score?session_id=<id>
    Возвращает текущий счёт и статистику сессии.

    Ответ:
        {
          "session_id":    "...",
          "mode":          "constellation",
          "difficulty":    "medium",
          "score":         1200,
          "round":         5,
          "total_rounds":  10,
          "correct_count": 4,
          "accuracy":      80,
          "streak":        2,
          "best_streak":   3,
          "rank":          "🔭 Sky Watcher"
        }
    """
    session_id = request.args.get("session_id", "")
    session    = get_session(session_id)
    if not session:
        return _err("Session not found", 404)
    return jsonify({**session.to_dict(), "rank": get_rank(session.score)})


@game_bp.route("/api/finish", methods=["POST"])
def api_finish():
    """
    POST /game/api/finish
    Явно завершает сессию и возвращает итоговую статистику.
    После вызова session_id становится недействительным.

    Тело запроса: { "session_id": "..." }

    Ответ:
        {
          ...поля /api/score...,
          "rank":    "⭐ Star Navigator",
          "history": [{ "round": 1, "correct": true, "points": 240, "answer": "Orion" }, ...]
        }
    """
    data       = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "")
    session    = get_session(session_id)
    if not session:
        return _err("Session not found", 404)

    summary = {
        **session.to_dict(),
        "rank":    get_rank(session.score),
        "history": session.history,
    }
    delete_session(session_id)
    return jsonify(summary)