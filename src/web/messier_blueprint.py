"""
Messier Game — Flask Blueprint
Файл: src/web/messier_blueprint.py
"""

import io
import random
import uuid
from datetime import datetime
from threading import Lock
from typing import Any, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from flask import Blueprint, jsonify, request, send_file

from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.messier.messier_catalog import MessierCatalog, MessierType
from src.pinhole_projection.pinhole_projector import (
    CameraConfig,
    ConstellationConfig,
    Pinhole,
    PinholeConfig,
    ShotConditions,
)
from src.planets_catalog.planet_catalog import PlanetCatalog

# ── FIX 1: Закрываем все figure, которые matplotlib мог создать при импорте,
#           чтобы первый рендер не «унаследовал» мусорное состояние.
matplotlib.use("Agg")
plt.close("all")

# ── Blueprint ───────────────────────────────────────────────────────────────
messier_bp = Blueprint("messier", __name__)

# ── Каталоги (инициализируются один раз при первом запросе) ─────────────────
_star_catalog = None
_planet_catalog = None
_messier_catalog = None
_catalogs_lock = Lock()  # отдельный лок для инициализации каталогов


def _get_catalogs():
    global _star_catalog, _planet_catalog, _messier_catalog
    if _star_catalog is None:
        with _catalogs_lock:
            # double-checked locking
            if _star_catalog is None:
                _star_catalog = Catalog(
                    catalog_name="hip_data.tsv", use_cache=True
                )
                _planet_catalog = PlanetCatalog()
                _messier_catalog = MessierCatalog()
                plt.close("all")
    return _star_catalog, _planet_catalog, _messier_catalog


# ── Хранилище сессий ────────────────────────────────────────────────────────
_sessions: Dict[str, Any] = {}
_lock = Lock()


# ── Вспомогательные функции ─────────────────────────────────────────────────


def _new_session(num_rounds: int) -> dict:
    _, _, mc = _get_catalogs()
    all_objs = list(mc.get_all_objects())
    chosen = random.sample(all_objs, min(num_rounds, len(all_objs)))
    return {
        "rounds": chosen,
        "current": 0,
        "score": 0,
        "results": [],
    }


def _render_png(messier_object) -> bytes:
    """Рендерит pinhole-проекцию объекта в PNG-байты."""
    # явно закрываем все висящие figure перед новым рендером
    plt.close("all")

    star_catalog, planet_catalog, mc = _get_catalogs()

    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=60,
        aspect_ratio=1.5,
        height_pix=600,
    )

    direction = np.array(
        [
            float(messier_object["x"]),
            float(messier_object["y"]),
            float(messier_object["z"]),
        ],
        dtype=np.float32,
    )

    shot_cond = ShotConditions(center_direction=direction, tilt_angle=0.0)

    const_cfg = ConstellationConfig(
        constellation_color="lightgray",
        constellation_linewidth=0.8,
        constellation_alpha=0.6,
    )

    config = PinholeConfig(
        local_time=datetime(2024, 1, 1, 0, 0, 0),
        add_ticks=False,
        use_dark_mode=True,
        add_planets=False,
        add_ecliptic=False,
        add_equator=False,
        add_galactic_equator=False,
        add_equatorial_grid=False,
        add_constellations=True,
        add_constellations_names=True,
    )

    projector = Pinhole(
        shot_cond=shot_cond,
        camera_cfg=camera_cfg,
        config=config,
        constellation_config=const_cfg,
        catalog=star_catalog,
        planet_catalog=planet_catalog,
    )

    fig, ax = projector.generate(
        constraints=CatalogConstraints(max_magnitude=5.5)
    )
    ax.set_aspect("equal")

    # Маркер объекта
    cx, cy = camera_cfg.width / 2, camera_cfg.height / 2
    ms = max(20, min(200, float(messier_object["size"]) * 2))
    color = mc.get_type_color(MessierType(messier_object["obj_type"]))
    ax.scatter(
        cx,
        cy,
        s=ms,
        marker="o",
        facecolors="none",
        edgecolors=color,
        linewidths=2.5,
        alpha=0.9,
    )
    ax.scatter(cx, cy, s=15, marker=".", c=color, alpha=1.0)

    obj_type = mc.get_type_name(MessierType(messier_object["obj_type"]))
    ax.set_title(
        f"Тип: {obj_type}  |  Зв. вел.: {messier_object['v_mag']:.1f}  "
        f"|  Угл. размер: {messier_object['size']:.1f}'  "
        f"|  Созвездие: {messier_object['constellation']}",
        fontsize=10,
        pad=14,
        color="white",
    )
    fig.patch.set_facecolor("#0a0e1a")

    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=100,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── CORS ────────────────────────────────────────────────────────────────────


@messier_bp.after_request
def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@messier_bp.route("/api/messier/<path:_>", methods=["OPTIONS"])
def _options(_):
    return jsonify({}), 200


# ── Маршруты ────────────────────────────────────────────────────────────────


@messier_bp.route("/api/messier/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}
    num_rounds = max(1, min(110, int(data.get("num_rounds", 5))))
    sid = str(uuid.uuid4())
    session = _new_session(num_rounds)

    with _lock:
        _sessions[sid] = session

    return jsonify({"session_id": sid, "num_rounds": len(session["rounds"])})


@messier_bp.route("/api/messier/image")
def image():
    sid = request.args.get("session_id")
    with _lock:
        session = _sessions.get(sid)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    idx = session["current"]
    if idx >= len(session["rounds"]):
        return jsonify({"error": "Игра завершена"}), 400

    png = _render_png(session["rounds"][idx])
    resp = send_file(io.BytesIO(png), mimetype="image/png")
    # запрещаем кэширование изображений на прокси/nginx,
    # чтобы каждый раунд показывал новый объект
    resp.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    resp.headers["Pragma"] = "no-cache"
    return resp


@messier_bp.route("/api/messier/answer", methods=["POST"])
def answer():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")

    with _lock:
        session = _sessions.get(sid)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    try:
        guess = int(data.get("guess"))
    except (TypeError, ValueError):
        return jsonify({"error": "Некорректное число"}), 400

    idx = session["current"]
    if idx >= len(session["rounds"]):
        return jsonify({"error": "Игра завершена"}), 400

    _, _, mc = _get_catalogs()
    obj = session["rounds"][idx]
    correct = int(obj["m_number"])
    is_ok = guess == correct

    if is_ok:
        session["score"] += 1

    session["results"].append(
        {
            "round": idx + 1,
            "guess": guess,
            "correct": correct,
            "is_correct": is_ok,
        }
    )
    session["current"] += 1
    game_over = session["current"] >= len(session["rounds"])

    try:
        raw_name = obj["name"]
        name = (
            str(raw_name).strip()
            if raw_name and str(raw_name).strip()
            else None
        )
    except Exception:
        name = None
    obj_type = mc.get_type_name(MessierType(obj["obj_type"]))

    return jsonify(
        {
            "correct": is_ok,
            "correct_number": correct,
            "guess": guess,
            "name": name,
            "type": obj_type,
            "constellation": str(obj["constellation"]),
            "magnitude": float(obj["v_mag"]),
            "size": float(obj["size"]),
            "score": session["score"],
            "round": idx + 1,
            "total_rounds": len(session["rounds"]),
            "game_over": game_over,
        }
    )


@messier_bp.route("/api/messier/score")
def score():
    sid = request.args.get("session_id")
    with _lock:
        session = _sessions.get(sid)

    if not session:
        return jsonify({"error": "Сессия не найдена"}), 404

    return jsonify(
        {
            "score": session["score"],
            "total": len(session["rounds"]),
            "results": session["results"],
        }
    )
