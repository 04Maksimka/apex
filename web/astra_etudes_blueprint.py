"""
Flask Blueprint: /astra-etudes/*
Интерактивные астрономические сценарии (AstraEtudes).

Регистрация в app.py (два blueprint-а):
    from astrageek.web.astra_etudes_blueprint import (
        astra_etudes_bp, compute_bp
    )
    app.register_blueprint(astra_etudes_bp)
    app.register_blueprint(compute_bp)        # маршрут /api/compute

URL-схема
---------
GET /astra-etudes/          →  хаб со списком сценариев
GET /astra-etudes/lobby     →  алиас хаба
GET /astra-etudes/<slug>    →  конкретный сценарий (astra-etudes/<slug>.html)
GET /api/compute            →  вычисление траектории (орбитальный симулятор)
"""

from __future__ import annotations

import math
import os

from flask import Blueprint, abort, jsonify, request, send_from_directory

astra_etudes_bp = Blueprint(
    "astra_etudes", __name__, url_prefix="/astra-etudes"
)

# compute_bp регистрируется без префикса — отвечает на /api/compute
compute_bp = Blueprint("compute", __name__)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static", "astra-etudes")

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
# Физические константы
# ---------------------------------------------------------------------------
GM = 3.986004418e14  # м^3/с^2
R_EARTH = 6.371e6  # м
G_SURFACE = 9.80665  # м/с^2
MAX_R = 1.5e9  # м  — дальность «побега»
MAX_TIME = 6 * 3600  # с  — максимум 6 часов интеграции


# ---------------------------------------------------------------------------
# Числовая механика (RK4)
# ---------------------------------------------------------------------------


def _rk4_step(state, dt):
    """Один шаг RK4 для {x, y, vx, vy} в поле тяготения Земли."""

    def deriv(s):
        x, y, vx, vy = s
        r2 = x * x + y * y
        r = math.sqrt(r2)
        a = -GM / r2
        return (vx, vy, a * x / r, a * y / r)

    x0, y0, vx0, vy0 = state
    k1 = deriv(state)
    k2 = deriv(
        (
            x0 + k1[0] * dt / 2,
            y0 + k1[1] * dt / 2,
            vx0 + k1[2] * dt / 2,
            vy0 + k1[3] * dt / 2,
        )
    )
    k3 = deriv(
        (
            x0 + k2[0] * dt / 2,
            y0 + k2[1] * dt / 2,
            vx0 + k2[2] * dt / 2,
            vy0 + k2[3] * dt / 2,
        )
    )
    k4 = deriv(
        (x0 + k3[0] * dt, y0 + k3[1] * dt, vx0 + k3[2] * dt, vy0 + k3[3] * dt)
    )
    return (
        x0 + dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]),
        y0 + dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]),
        vx0 + dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]),
        vy0 + dt / 6 * (k1[3] + 2 * k2[3] + 2 * k3[3] + k4[3]),
    )


def _compute_trajectory_rk4(r0x, r0y, v0x, v0y):
    """Интегрирует траекторию методом RK4 до касания Земли или улёта."""
    state = (r0x, r0y, v0x, v0y)
    pts = [[r0x, r0y]]
    t = 0.0
    dt = 2.0
    MAX_PTS = 8000

    while t < MAX_TIME and len(pts) < MAX_PTS:
        nx, ny, nvx, nvy = _rk4_step(state, dt)
        r = math.sqrt(nx * nx + ny * ny)

        if r < R_EARTH:
            # Интерполируем точку касания поверхности
            x0, y0 = state[0], state[1]
            r0_ = math.sqrt(x0 * x0 + y0 * y0)
            frac = (r0_ - R_EARTH) / max(r0_ - r, 1e-3)
            pts.append([x0 + frac * (nx - x0), y0 + frac * (ny - y0)])
            break

        if r > MAX_R:
            pts.append([nx, ny])
            break

        pts.append([nx, ny])
        state = (nx, ny, nvx, nvy)
        t += dt

        # Адаптивный шаг: вблизи Земли — мельче
        if r < R_EARTH * 1.05:
            dt = 0.2
        elif r < R_EARTH * 1.2:
            dt = 1.0
        else:
            dt = 2.0

    return pts


def _compute_conic(r0x, r0y, v0x, v0y, n_points=6000):
    """Аналитическое коническое сечение через интегралы движения."""
    r0 = math.sqrt(r0x**2 + r0y**2)
    v0sq = v0x**2 + v0y**2

    E = v0sq / 2 - GM / r0
    L = r0x * v0y - r0y * v0x

    if abs(L) < 1.0:
        return []

    p = L**2 / GM
    ecc_sq = max(0.0, 1 + 2 * E * L**2 / (GM**2))
    ecc = math.sqrt(ecc_sq)

    # Направление перицентра (вектор Лапласа–Рунге–Ленца)
    Ax = v0y * L - GM * r0x / r0
    Ay = -v0x * L - GM * r0y / r0
    A_norm = math.sqrt(Ax**2 + Ay**2)
    if A_norm < 1e-6:
        ex_hat, ey_hat = 1.0, 0.0
    else:
        ex_hat, ey_hat = Ax / A_norm, Ay / A_norm
    px_hat, py_hat = -ey_hat, ex_hat

    if ecc < 1.0:
        raw = [2 * math.pi * i / n_points for i in range(n_points + 1)]
        thetas = [
            math.copysign(abs(t) ** 0.65 * math.pi**0.35, t)
            if t <= math.pi
            else 2 * math.pi - (2 * math.pi - t) ** 0.65 * math.pi**0.35
            for t in raw
        ]
    elif ecc < 1.0001:
        # Парабола — плотнее у вершины
        raw = [i / n_points for i in range(n_points + 1)]
        thetas = [-2.8 + 5.6 * (r**0.5) for r in raw]
    else:
        theta_max = math.acos(min(1.0, -1.0 / ecc)) * 0.97
        raw = [i / n_points for i in range(n_points + 1)]
        # Плотнее у перицентра (θ=0)
        thetas = [-theta_max + 2 * theta_max * (r**0.55) for r in raw]

    pts = []
    for theta in thetas:
        denom = 1 + ecc * math.cos(theta)
        if abs(denom) < 1e-9:
            continue
        r = p / denom
        if r < 0 or r > MAX_R * 2:
            continue
        x = r * (math.cos(theta) * ex_hat + math.sin(theta) * px_hat)
        y = r * (math.cos(theta) * ey_hat + math.sin(theta) * py_hat)
        pts.append([x, y])

    return pts


def _compute_flat(r0x, r0y, v0x, v0y, n_points=400):
    """Параболическая траектория (плоская Земля, g=const)."""
    r0 = math.sqrt(r0x**2 + r0y**2)

    up_x, up_y = r0x / r0, r0y / r0
    hor_x, hor_y = -r0y / r0, r0x / r0

    vh = v0x * hor_x + v0y * hor_y
    vv = v0x * up_x + v0y * up_y
    h0 = r0 - R_EARTH

    g = G_SURFACE
    disc = vv**2 + 2 * g * h0
    if disc < 0:
        t_end = 3000.0
    else:
        t_land = (vv + math.sqrt(disc)) / g
        t_end = min(t_land, 3000.0)

    pts = []
    for i in range(n_points + 1):
        t = t_end * i / n_points
        xh = vh * t
        xv = h0 + vv * t - 0.5 * g * t**2
        if xv < 0:
            if i > 0:
                t_prev = t_end * (i - 1) / n_points
                xv_prev = h0 + vv * t_prev - 0.5 * g * t_prev**2
                xh_prev = vh * t_prev
                frac = xv_prev / max(xv_prev - xv, 1e-9)
                xh_land = xh_prev + frac * (xh - xh_prev)
                pts.append([r0x + xh_land * hor_x, r0y + xh_land * hor_y])
            break
        pts.append(
            [r0x + xh * hor_x + xv * up_x, r0y + xh * hor_y + xv * up_y]
        )

    return pts


def _orbital_elements(r0x, r0y, v0x, v0y):
    """Вычислить орбитальные элементы."""
    r0 = math.sqrt(r0x**2 + r0y**2)
    v0sq = v0x**2 + v0y**2
    E = v0sq / 2 - GM / r0
    L = r0x * v0y - r0y * v0x

    ecc_sq = max(0.0, 1 + 2 * E * L**2 / (GM**2))
    ecc = math.sqrt(ecc_sq)

    a = -GM / (2 * E) if E != 0 else float("inf")

    r_peri = a * (1 - ecc) if E < 0 else None
    r_apo = a * (1 + ecc) if E < 0 else None
    T = 2 * math.pi * math.sqrt(a**3 / GM) if (E < 0 and a > 0) else None

    vorb = math.sqrt(GM / r0)
    vesc = math.sqrt(2 * GM / r0)

    return {
        "ecc": ecc,
        "r_peri": r_peri,
        "r_apo": r_apo,
        "period": T,
        "E": E,
        "vorb": vorb,
        "vesc": vesc,
    }


# ---------------------------------------------------------------------------
# Страничные маршруты (astra_etudes_bp)
# ---------------------------------------------------------------------------


@astra_etudes_bp.route("/")
@astra_etudes_bp.route("/lobby")
def hub():
    """Хаб со всеми сценариями."""
    return send_from_directory(_STATIC_DIR, "index.html")


@astra_etudes_bp.route("/<slug>")
def scenario_page(slug: str):
    filename = f"{slug}.html"
    path = os.path.join(_STATIC_DIR, filename)
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(_STATIC_DIR, filename)


@astra_etudes_bp.route("/api/scenarios")
def api_scenarios():
    return jsonify(SCENARIOS_META)


# ---------------------------------------------------------------------------
# /api/compute  (compute_bp — без префикса, подключается в app.py отдельно)
# ---------------------------------------------------------------------------


@compute_bp.route("/api/compute")
def api_compute():
    """
    GET /api/compute?speed=<м/с>&angle=<°>&height=<км>

    Ответ JSON:
      trajectory  — [[x,y], …]  RK4-траектория
      conic       — [[x,y], …]  аналитическая орбита
      flat        — [[x,y], …]  парабола плоской Земли
      r0, v0      — начальные условия
      ecc, r_peri, r_apo, period, E, vorb, vesc — орбитальные элементы
    """
    try:
        speed = float(request.args.get("speed", 3000))
        angle_d = float(request.args.get("angle", 45))
        height_m = float(request.args.get("height", 0)) * 1000.0
    except (TypeError, ValueError):
        return jsonify({"error": "Неверные параметры"}), 400

    # Начальная позиция: над точкой θ=90° (вершина Земли)
    r0x = 0.0
    r0y = R_EARTH + height_m

    angle_r = math.radians(angle_d)
    v0x = speed * math.cos(angle_r)
    v0y = speed * math.sin(angle_r)

    traj = _compute_trajectory_rk4(r0x, r0y, v0x, v0y)
    conic = _compute_conic(r0x, r0y, v0x, v0y)
    flat = _compute_flat(r0x, r0y, v0x, v0y)
    el = _orbital_elements(r0x, r0y, v0x, v0y)

    # Прореживаем при большом количестве точек
    if len(traj) > 3000:
        step = max(1, len(traj) // 3000)
        traj = traj[::step]

    return jsonify(
        {
            "trajectory": traj,
            "conic": conic,
            "flat": flat,
            "r0": [r0x, r0y],
            "v0": [v0x, v0y],
            "ecc": el["ecc"],
            "r_peri": el["r_peri"],
            "r_apo": el["r_apo"],
            "period": el["period"],
            "E": el["E"],
            "vorb": el["vorb"],
            "vesc": el["vesc"],
        }
    )
