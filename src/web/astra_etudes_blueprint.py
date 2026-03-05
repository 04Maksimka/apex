"""
Flask Blueprint: /astra-etudes/*
Интерактивные астрономические сценарии (AstraEtudes).

Регистрация в app.py:
    from src.web.astra_etudes_blueprint import astra_etudes_bp
    app.register_blueprint(astra_etudes_bp)

URL-схема
---------
GET /astra-etudes/          →  хаб со списком сценариев
GET /astra-etudes/lobby     →  алиас хаба
GET /astra-etudes/<slug>    →  конкретный сценарий (astra-etudes/<slug>.html)

Как добавить новый сценарий
---------------------------
1. Положить HTML-файл в  src/web/public_html/astra-etudes/<slug>.html
2. Добавить запись в массив SCENARIOS_META (используется /astra-etudes/api/scenarios)
3. Ссылка /astra-etudes/<slug> начнёт работать автоматически
"""

from __future__ import annotations

import os

from flask import Blueprint, abort, jsonify, send_from_directory

astra_etudes_bp = Blueprint(
    "astra_etudes", __name__, url_prefix="/astra-etudes"
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "public_html", "astra-etudes")

# ---------------------------------------------------------------------------
# Мета-информация о сценариях
# ---------------------------------------------------------------------------
SCENARIOS_META = [
    {
        "id": "orbital-simulator",
        "title": "Орбитальный симулятор",
        "description": "Бросок тела в гравитационном поле Земли. "
                       "Численная траектория RK4, орбитальные элементы, конические сечения.",
        "tag": "mechanics",
        "tag_label": "Механика",
        "difficulty": 2,
        "enabled": True,
    },
    {
        "id": "lunar-phases",
        "title": "Фазы Луны",
        "description": "Геометрия освещения спутника. "
                       "Зависимость наблюдаемой фазы от взаимного расположения тел.",
        "tag": "optics",
        "tag_label": "Оптика",
        "difficulty": 1,
        "enabled": False,
    },
    {
        "id": "doppler-star",
        "title": "Эффект Доплера в спектре",
        "description": "Сдвиг спектральных линий при движении звезды. "
                       "Определение лучевой скорости.",
        "tag": "waves",
        "tag_label": "Волны",
        "difficulty": 2,
        "enabled": False,
    },
    {
        "id": "black-body",
        "title": "Закон Планка",
        "description": "Излучение абсолютно чёрного тела. "
                       "Кривые спектральной яркости, законы Вина и Стефана–Больцмана.",
        "tag": "stellar",
        "tag_label": "Звёзды",
        "difficulty": 3,
        "enabled": False,
    },
    {
        "id": "eclipse",
        "title": "Затмения",
        "description": "Солнечное и лунное затмения. "
                       "Геометрия тени, зона полной и частичной тени.",
        "tag": "optics",
        "tag_label": "Оптика",
        "difficulty": 2,
        "enabled": False,
    },
    {
        "id": "binary-star",
        "title": "Двойные звёзды",
        "description": "Гравитационно связанная пара звёзд. "
                       "Вращение вокруг центра масс, закон Кеплера.",
        "tag": "stellar",
        "tag_label": "Звёзды",
        "difficulty": 3,
        "enabled": False,
    },
]

# ---------------------------------------------------------------------------
# Страничные маршруты
# ---------------------------------------------------------------------------


@astra_etudes_bp.route("/")
@astra_etudes_bp.route("/lobby")
def hub():
    """Хаб со всеми сценариями."""
    return send_from_directory(_STATIC_DIR, "index.html")


@astra_etudes_bp.route("/<slug>")
def scenario_page(slug: str):
    """Конкретный сценарий: /astra-etudes/<slug> → astra-etudes/<slug>.html"""
    filename = f"{slug}.html"
    path = os.path.join(_STATIC_DIR, filename)
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(_STATIC_DIR, filename)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@astra_etudes_bp.route("/api/scenarios")
def api_scenarios():
    """Список всех сценариев с мета-информацией."""
    return jsonify(SCENARIOS_META)
