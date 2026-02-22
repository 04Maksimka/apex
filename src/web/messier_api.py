"""
Messier Object Guessing Game — Flask API
Размещать: src/web/messier_api.py

Запуск:
    cd <project_root>
    pip install flask
    python src/web/messier_api.py

API:
    POST /api/messier/start          — начать новую игру
    GET  /api/messier/image          — получить PNG-изображение текущего объекта
    POST /api/messier/answer         — отправить ответ
    GET  /api/messier/score          — получить итог
"""

import io
import uuid
import random
import base64
from datetime import datetime
from threading import Lock
from typing import Dict, Any

# Использовать Agg-бэкенд ДО импорта pyplot, чтобы matplotlib не требовал GUI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify, send_file
from flask import make_response

from src.messier.messier_catalog import MessierCatalog, MessierType
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.pinhole_projection.pinhole_projector import (
    ShotConditions, CameraConfig, Pinhole, PinholeConfig, ConstellationConfig
)
from src.planets_catalog.planet_catalog import PlanetCatalog

app = Flask(__name__)

# ── Хранилище сессий (in-memory, подходит для небольшой нагрузки) ─────────────
sessions: Dict[str, Any] = {}
sessions_lock = Lock()

# ── Разделяемые каталоги (инициализируются один раз) ─────────────────────────
star_catalog = Catalog(catalog_name="hip_data.tsv", use_cache=True)
planet_catalog = PlanetCatalog()
messier_catalog = MessierCatalog()


def _make_session(num_rounds: int) -> dict:
    """Создать новую игровую сессию."""
    all_objects = messier_catalog.get_all_objects()
    chosen = random.sample(list(all_objects), min(num_rounds, len(all_objects)))
    return {
        "rounds": chosen,          # список объектов
        "current": 0,              # текущий раунд
        "score": 0,
        "answered": False,         # ожидаем ли мы ответ прямо сейчас
        "results": [],             # история ответов
    }


def _render_pinhole_png(messier_object) -> bytes:
    """Рендерит pinhole-проекцию объекта в PNG-байты."""
    camera_config = CameraConfig.from_fov_and_aspect(
        fov_deg=60,
        aspect_ratio=1.5,
        height_pix=600,
    )

    ra  = float(messier_object["ra"])
    dec = float(messier_object["dec"])

    import numpy as np
    direction = np.array([
        np.cos(dec) * np.cos(ra),
        np.cos(dec) * np.sin(ra),
        np.sin(dec),
    ])

    shot_cond = ShotConditions(
        center_direction=direction,
        tilt_angle=0.0,
    )

    constellation_config = ConstellationConfig(
        constellation_linewidth=0.5,
        constellation_alpha=0.5,
    )

    config = PinholeConfig()
    projector = Pinhole(
        shot_cond=shot_cond,
        camera_cfg=camera_config,
        config=config,
        constellation_config=constellation_config,
        catalog=star_catalog,
        planet_catalog=planet_catalog,
    )

    constraints = CatalogConstraints(max_magnitude=6.5)
    fig, ax = projector.generate(constraints=constraints)
    ax.set_aspect("equal")

    # Маркер объекта
    cx = camera_config.width  / 2
    cy = camera_config.height / 2
    marker_size = max(20, min(200, float(messier_object["size"]) * 2))
    color = MessierCatalog.get_type_color(MessierType(messier_object["obj_type"]))
    ax.scatter(cx, cy, s=marker_size, marker="o",
               facecolors="none", edgecolors=color, linewidths=2, alpha=0.8)
    ax.scatter(cx, cy, s=10, marker=".", c=color, alpha=0.9)

    # Подпись (без номера объекта — это загадка)
    obj_type = MessierCatalog.get_type_name(MessierType(messier_object["obj_type"]))
    ax.set_title(
        f"Тип: {obj_type}  |  Зв. вел.: {messier_object['v_mag']:.1f}  "
        f"|  Угл. размер: {messier_object['size']:.1f}'  "
        f"|  Созвездие: {messier_object['constellation']}",
        fontsize=10, pad=14, color="white"
    )
    fig.patch.set_facecolor("#0a0e1a")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/api/messier/<path:_>", methods=["OPTIONS"])
def options_handler(_):
    return jsonify({}), 200


@app.route("/api/messier/start", methods=["POST"])
def start_game():
    """
    Body (JSON): { "num_rounds": 5 }
    Response:    { "session_id": "...", "num_rounds": 5 }
    """
    data = request.get_json(silent=True) or {}
    num_rounds = max(1, min(110, int(data.get("num_rounds", 5))))

    session_id = str(uuid.uuid4())
    session = _make_session(num_rounds)

    with sessions_lock:
        sessions[session_id] = session

    return jsonify({
        "session_id": session_id,
        "num_rounds": len(session["rounds"]),
    })


@app.route("/api/messier/image", methods=["GET"])
def get_image():
    """
    Query: ?session_id=...
    Returns PNG image of the current Messier object.
    """
    session_id = request.args.get("session_id")
    with sessions_lock:
        session = sessions.get(session_id)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    idx = session["current"]
    if idx >= len(session["rounds"]):
        return jsonify({"error": "Игра уже завершена"}), 400

    obj = session["rounds"][idx]
    png = _render_pinhole_png(obj)
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.route("/api/messier/answer", methods=["POST"])
def submit_answer():
    """
    Body: { "session_id": "...", "guess": 42 }
    Response: {
        "correct": bool,
        "correct_number": int,
        "name": str,
        "type": str,
        "constellation": str,
        "score": int,
        "round": int,
        "total_rounds": int,
        "game_over": bool
    }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    guess = data.get("guess")

    with sessions_lock:
        session = sessions.get(session_id)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    try:
        guess = int(guess)
    except (TypeError, ValueError):
        return jsonify({"error": "Некорректное число"}), 400

    idx = session["current"]
    if idx >= len(session["rounds"]):
        return jsonify({"error": "Игра уже завершена"}), 400

    obj = session["rounds"][idx]
    correct = int(obj["m_number"])
    is_correct = guess == correct

    if is_correct:
        session["score"] += 1

    obj_type = MessierCatalog.get_type_name(MessierType(obj["obj_type"]))
    name = str(obj.get("name", "")) if obj.get("name") else None

    session["results"].append({
        "round": idx + 1,
        "guess": guess,
        "correct": correct,
        "is_correct": is_correct,
    })
    session["current"] += 1
    game_over = session["current"] >= len(session["rounds"])

    return jsonify({
        "correct": is_correct,
        "correct_number": correct,
        "name": name,
        "type": obj_type,
        "constellation": str(obj["constellation"]),
        "magnitude": float(obj["v_mag"]),
        "size": float(obj["size"]),
        "score": session["score"],
        "round": idx + 1,
        "total_rounds": len(session["rounds"]),
        "game_over": game_over,
    })


@app.route("/api/messier/score", methods=["GET"])
def get_score():
    """
    Query: ?session_id=...
    Response: { "score": int, "total": int, "results": [...] }
    """
    session_id = request.args.get("session_id")
    with sessions_lock:
        session = sessions.get(session_id)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    return jsonify({
        "score": session["score"],
        "total": len(session["rounds"]),
        "results": session["results"],
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
