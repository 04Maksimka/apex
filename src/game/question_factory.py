"""
Question factory for all 5 AstraGeek Sky Quiz game modes.

Modes:
  1. constellation — Guess the constellation from a pinhole image (no labels)
  2. star          — Name the highlighted bright star
  3. messier       — Identify the Messier deep-sky object
  4. draw          — Connect stars to draw the constellation
  5. trivia        — Answer trivia and find the described constellation on a map
"""
from __future__ import annotations

import io
import base64
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.messier.messier_catalog import MessierCatalog, MessierType
from src.pinhole_projection.pinhole_projector import (
    CameraConfig, ShotConditions, PinholeConfig, Pinhole, ConstellationConfig,
)
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.constellations_metadata.constellations_data import (
    CONSTELLATIONS_DATA,
    get_constellation_lines,
    get_constellation_center,
    get_available_constellations,
)
from src.game.session import DIFFICULTY_CONSTELLATIONS, DIFFICULTY_MAGNITUDE

# ---------------------------------------------------------------------------
# Module-level singletons (loaded once per process)
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parents[2]
_HIP_CATALOG: Optional[Catalog] = None
_PLANET_CATALOG: Optional[PlanetCatalog] = None
_MESSIER_CATALOG: Optional[MessierCatalog] = None
_NAMED_STARS: Dict[int, str] = {}  # hip_id -> star_name

OBS_TIME = datetime(2024, 6, 21, 0, 0, 0)

# ---------------------------------------------------------------------------
# Fun-fact libraries
# ---------------------------------------------------------------------------
CONSTELLATION_FACTS: Dict[str, str] = {
    "ORI": "Орион содержит две из самых ярких звёзд неба — красный гигант Бетельгейзе и голубой сверхгигант Ригель.",
    "UMA": "Большая Медведица содержит Большой Ковш — один из самых узнаваемых астеризмов северного неба.",
    "CAS": "Кассиопея имеет форму буквы W или M и никогда не заходит за горизонт для жителей средних широт.",
    "CYG": "Лебедь содержит яркую звезду Денеб — одну из самых далёких и светлых в Летнем треугольнике.",
    "LEO": "Лев — знак зодиака, в котором находится галактика M66 из триплета Льва.",
    "SCO": "Скорпион украшен красным Антаресом — звездой, настолько огромной, что она вмещала бы орбиту Марса.",
    "GEM": "Близнецы названы в честь Кастора и Поллукса — мифических братьев-полубогов.",
    "TAU": "В Тельце находится Крабовидная туманность M1 — остаток сверхновой, наблюдавшейся в 1054 году.",
    "AQL": "В Орле находится Альтаир — одна из трёх звёзд Летнего треугольника.",
    "LYR": "Лира содержит Вегу — пятую по яркости звезду неба и полюс мира около 12 000 лет назад.",
    "PER": "Персей содержит «Демонскую звезду» Алголь — ярчайшую затменно-переменную звезду.",
    "AUR": "В Возничем находится Капелла — шестая по яркости звезда неба и тройная звёздная система.",
    "VIR": "Дева — крупнейшее зодиакальное созвездие; в нём расположен Скопление Девы из ~1300 галактик.",
    "SGR": "Стрелец указывает в сторону центра Галактики; в нём более 15 объектов Мессье.",
    "AND": "В Андромеде находится галактика M31 — ближайшая к нам крупная галактика, видимая невооружённым глазом.",
    "BOO": "В Волопасе сияет Арктур — ярчайшая звезда северного полушария неба.",
    "HER": "В Геркулесе находится Великое шаровое скопление M13 — одно из красивейших в северном небе.",
    "DRA": "Дракон окружает Малую Медведицу; 5000 лет назад Тубан был звездой-полюсом.",
    "CRU": "Южный Крест — самое маленькое по площади созвездие, ориентир в Южном полушарии.",
    "UMI": "В Малой Медведице находится Полярная звезда — в 430 световых годах от нас.",
}

STAR_FACTS: Dict[str, str] = {
    "Sirius":     "Сириус — самая яркая звезда ночного неба (−1,46m), двойная система на расстоянии 8,6 св. лет.",
    "Vega":       "Вега — одна из вершин Летнего треугольника; была Полярной звездой около 14 000 лет назад.",
    "Arcturus":   "Арктур — ярчайшая звезда северного полушария; красный гигант в 37 св. годах от нас.",
    "Capella":    "Капелла — тройная система из двух жёлтых гигантов и пары красных карликов.",
    "Rigel":      "Ригель — голубой сверхгигант, светимость которого в 120 000 раз превышает солнечную.",
    "Procyon":    "Процион — двойная система: яркий субгигант и белый карлик в 11,5 св. годах.",
    "Betelgeuse": "Бетельгейзе — красный сверхгигант на грани взрыва сверхновой; его диаметр больше орбиты Юпитера.",
    "Altair":     "Альтаир вращается так быстро (286 км/с), что сплюснута в экваторе на 20%.",
    "Aldebaran":  "Альдебаран — оранжевый гигант, «глаз» Тельца; в 65 св. годах от Земли.",
    "Spica":      "Спика — ярчайшая звезда Девы и двойная система: обе звезды деформированы приливными силами.",
    "Antares":    "Антарес — «соперник Марса»; красный сверхгигант диаметром ~700 солнечных.",
    "Pollux":     "Поллукс — ярчайшая звезда Близнецов; известна экзопланета Поллукс b.",
    "Deneb":      "Денеб — один из самых далёких «ярких» объектов неба: ~2600 св. лет, светимость 200 000 Солнц.",
    "Regulus":    "Регулус — сердце Льва; быстро вращающаяся звезда, почти достигшая критической скорости распада.",
    "Polaris":    "Полярная звезда отстоит от полюса мира примерно на 0,7° и медленно к нему приближается.",
}

MESSIER_FACTS: Dict[int, str] = {
    1:  "M1 (Крабовидная туманность) — остаток сверхновой 1054 года; в её центре нейтронная звезда-пульсар.",
    31: "M31 (Туманность Андромеды) — ближайшая к нам крупная галактика, через ~4 млрд лет сольётся с Млечным Путём.",
    42: "M42 (Туманность Ориона) — активная область звездообразования в 1344 св. годах.",
    45: "Плеяды (M45) — молодое рассеянное скопление; большинство звёзд образовалось ~100 млн лет назад.",
    13: "M13 — Великое шаровое скопление Геркулеса: 300 000 звёзд в 22 200 св. годах.",
    51: "M51 (Галактика Водоворот) — первая галактика, у которой обнаружена спиральная структура (1845 г.).",
    57: "M57 (Кольцо Лиры) — планетарная туманность: умирающая звезда сбросила оболочку.",
    27: "M27 (Гантель) — первая открытая планетарная туманность (Мессье, 1764).",
    8:  "M8 (Лагунная туманность) — один из немногих объектов Мессье, видимых невооружённым глазом.",
}

TRIVIA_QUESTIONS: List[Dict[str, Any]] = [
    {
        "question": "Это созвездие содержит красного сверхгиганта Бетельгейзе и голубого сверхгиганта Ригель. В нём находится туманность M42.",
        "answer": "ORI",
        "hint": "Его пояс из трёх звёзд виден зимой",
    },
    {
        "question": "Созвездие с семью яркими звёздами, образующими «Большой Ковш». Две крайние звезды «указывают» на Полярную.",
        "answer": "UMA",
        "hint": "Медведица с длинным хвостом",
    },
    {
        "question": "Созвездие Летнего треугольника, в котором находится Вега — пятая по яркости звезда.",
        "answer": "LYR",
        "hint": "Музыкальный инструмент",
    },
    {
        "question": "Созвездие-«W» или «M», никогда не заходящее за горизонт в северных широтах. Названо в честь эфиопской царицы.",
        "answer": "CAS",
        "hint": "Гордая царица, посаженная на трон вверх ногами",
    },
    {
        "question": "В этом зодиакальном созвездии находится Антарес — «соперник Марса», краснее Марса по цвету.",
        "answer": "SCO",
        "hint": "Ядовитое членистоногое",
    },
    {
        "question": "Созвездие, в котором находится Альтаир — самый быстро вращающийся из ярких звёзд неба.",
        "answer": "AQL",
        "hint": "Птица-символ США",
    },
    {
        "question": "Ближайшая к нам крупная галактика M31 находится именно в этом созвездии. Осенью видна невооружённым глазом.",
        "answer": "AND",
        "hint": "Мифологическая принцесса, прикованная к скале",
    },
    {
        "question": "В этом созвездии сконцентрировано наибольшее число объектов Мессье; оно указывает на центр Галактики.",
        "answer": "SGR",
        "hint": "Полуконь-получеловек с луком",
    },
    {
        "question": "Созвездие с ярчайшей звездой северного полушария — Арктуром. Выглядит как «воздушный змей».",
        "answer": "BOO",
        "hint": "Пастух медведей",
    },
    {
        "question": "Созвездие, в котором находится Денеб — одна из самых далёких и светоносных звёзд видимых невооружённым глазом.",
        "answer": "CYG",
        "hint": "Белая водоплавающая птица",
    },
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _get_catalog() -> Catalog:
    global _HIP_CATALOG
    if _HIP_CATALOG is None:
        _HIP_CATALOG = Catalog(
            catalog_name=str(_BASE_DIR / "src" / "hip_catalog" / "hip_data.tsv"),
            use_cache=True,
        )
    return _HIP_CATALOG


def _get_planet_catalog() -> PlanetCatalog:
    global _PLANET_CATALOG
    if _PLANET_CATALOG is None:
        _PLANET_CATALOG = PlanetCatalog()
    return _PLANET_CATALOG


def _get_messier_catalog() -> MessierCatalog:
    global _MESSIER_CATALOG
    if _MESSIER_CATALOG is None:
        _MESSIER_CATALOG = MessierCatalog()
    return _MESSIER_CATALOG


def _load_named_stars() -> Dict[int, str]:
    global _NAMED_STARS
    if _NAMED_STARS:
        return _NAMED_STARS
    lines_path = _BASE_DIR / "src" / "constellations_metadata" / "lines_data.json"
    try:
        with open(lines_path, encoding="utf-8") as f:
            raw = json.load(f)
        for key, value in raw.items():
            if key.startswith("HIP "):
                hip_id = int(key.split(" ")[1])
                _NAMED_STARS[hip_id] = value[0]["english"]
    except Exception:
        pass
    return _NAMED_STARS


def _fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", dpi=100, bbox_inches="tight",
        facecolor=fig.get_facecolor(), edgecolor="none",
    )
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def _generate_pinhole_image(
    direction,          # ECI unit vector [x, y, z]
    magnitude: float,
    show_const: bool = True,
    show_names: bool = False,
    fov: float = 60.0,
    extra_draw=None,    # callable(fig, ax, camera_cfg) or None
) -> str:
    """
    Render a pinhole projection and return base64-encoded PNG.

    Correct API (matches messier_api.py and pinhole_projection_example.py):
        shot_cond  = ShotConditions(center_direction=..., tilt_angle=0.0)
        camera_cfg = CameraConfig.from_fov_and_aspect(fov_deg, aspect_ratio, height_pix)
        config     = PinholeConfig(local_time=..., add_constellations=..., ...)
        projector  = Pinhole(shot_cond, camera_cfg, config, catalog, planet_catalog,
                             constellation_config)
        fig, ax    = projector.generate(constraints)
    """
    direction = np.asarray(direction, dtype=np.float64)
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction = direction / norm

    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov,
        aspect_ratio=1.33,
        height_pix=600,
    )

    shot_cond = ShotConditions(
        center_direction=direction.astype(np.float32),
        tilt_angle=0.0,
    )

    config = PinholeConfig(
        local_time=OBS_TIME,
        add_constellations=show_const,
        add_constellations_names=show_names,
        add_ecliptic=False,
        add_equator=False,
        add_galactic_equator=False,
        add_planets=False,
        add_ticks=False,
        add_equatorial_grid=False,
        use_dark_mode=True,
    )

    constellation_config = ConstellationConfig() if show_const else None

    projector = Pinhole(
        shot_cond=shot_cond,
        camera_cfg=camera_cfg,
        config=config,
        catalog=_get_catalog(),
        planet_catalog=_get_planet_catalog(),
        constellation_config=constellation_config,
    )

    constraints = CatalogConstraints(max_magnitude=magnitude)
    fig, ax = projector.generate(constraints=constraints)

    if extra_draw is not None:
        extra_draw(fig, ax, camera_cfg)

    return _fig_to_base64(fig)


def _get_constellation_list(difficulty: str) -> List[str]:
    pool = DIFFICULTY_CONSTELLATIONS.get(difficulty)
    if pool is None:
        pool = get_available_constellations()
    available = set(CONSTELLATIONS_DATA.keys())
    return [c for c in pool if c in available]


def _random_distractors(correct: str, pool: List[str], n: int = 3) -> List[str]:
    candidates = [c for c in pool if c != correct]
    return random.sample(candidates, min(n, len(candidates)))


def _shuffle_options(*items: str) -> List[str]:
    opts = list(items)
    random.shuffle(opts)
    return opts


def _gnomonic_project(
    hip_ids: Set[int],
    center: np.ndarray,
    catalog: Catalog,
    magnitude: float,
) -> Dict[int, Dict[str, float]]:
    """Project constellation stars onto a 2-D tangent plane (gnomonic projection)."""
    z = center / np.linalg.norm(center)
    arb = np.array([0.0, 0.0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x_ax = np.cross(arb, z)
    x_ax /= np.linalg.norm(x_ax)
    y_ax = np.cross(z, x_ax)

    constraints = CatalogConstraints(max_magnitude=magnitude)
    stars = catalog.get_stars(constraints)
    hip_map = {int(s["hip_id"]): s for s in stars}

    result: Dict[int, Dict[str, float]] = {}
    for hip_id in hip_ids:
        s = hip_map.get(hip_id)
        if s is None:
            continue
        d = np.array([float(s["x"]), float(s["y"]), float(s["z"])])
        cos_t = float(np.dot(d, z))
        if cos_t < 0.05:
            continue
        px = float(np.dot(d, x_ax) / cos_t)
        py = float(np.dot(d, y_ax) / cos_t)
        result[hip_id] = {
            "hip_id": hip_id,
            "x": px,
            "y": py,
            "v_mag": float(s["v_mag"]),
        }
    return result


# ---------------------------------------------------------------------------
# Public API: QuestionFactory
# ---------------------------------------------------------------------------
class QuestionFactory:
    """Generates questions for each of the 5 game modes."""

    # ------------------------------------------------------------------
    # Mode 1 — Guess the Constellation
    # ------------------------------------------------------------------
    def make_constellation_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        pool = _get_constellation_list(session.difficulty)
        available = [c for c in pool if c not in session.used_objects]
        if not available:
            session.used_objects.clear()
            available = pool

        correct_abbr = random.choice(available)
        session.used_objects.add(correct_abbr)

        correct_name = CONSTELLATIONS_DATA[correct_abbr]["name"]
        # "center" in CONSTELLATIONS_DATA is already an ECI [x, y, z] unit vector
        center = CONSTELLATIONS_DATA[correct_abbr]["center"]

        image_b64 = _generate_pinhole_image(
            direction=center,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=60.0,
        )

        distractors = _random_distractors(correct_abbr, pool)
        dist_names = [CONSTELLATIONS_DATA[d]["name"] for d in distractors]
        options = _shuffle_options(correct_name, *dist_names)

        hint = f"Аббревиатура этого созвездия: {correct_abbr}"
        fun_fact = CONSTELLATION_FACTS.get(correct_abbr, f"Это созвездие — {correct_name}.")

        question = {
            "type": "constellation",
            "image": image_b64,
            "question": "Какое созвездие изображено на снимке?",
            "options": options,
            "correct": correct_name,
            "hint": hint,
            "fun_fact": fun_fact,
        }
        session.current_question = question
        return question

    # ------------------------------------------------------------------
    # Mode 2 — Name the Highlighted Star
    # ------------------------------------------------------------------
    def make_star_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        named_stars = _load_named_stars()
        catalog = _get_catalog()
        constraints = CatalogConstraints(max_magnitude=magnitude)
        stars_data = catalog.get_stars(constraints)

        available_hip = set(int(s["hip_id"]) for s in stars_data)
        candidates = {
            hip: name for hip, name in named_stars.items()
            if hip in available_hip and hip not in session.used_objects
        }
        if not candidates:
            session.used_objects.clear()
            candidates = {hip: name for hip, name in named_stars.items() if hip in available_hip}
        if not candidates:
            return self.make_constellation_question(session)

        correct_hip = random.choice(list(candidates.keys()))
        correct_name = candidates[correct_hip]
        session.used_objects.add(correct_hip)

        star_arr = next((s for s in stars_data if int(s["hip_id"]) == correct_hip), None)
        if star_arr is None:
            return self.make_constellation_question(session)

        # ECI direction from catalog
        direction = np.array(
            [float(star_arr["x"]), float(star_arr["y"]), float(star_arr["z"])],
            dtype=np.float64,
        )

        def _add_highlight(fig, ax, camera_cfg):
            # Star is at the image centre because camera points directly at it.
            # Pixel centre = (width/2, height/2)
            cx = camera_cfg.width / 2
            cy = camera_cfg.height / 2
            ax.plot(cx, cy, "o",
                    markersize=22, markerfacecolor="none",
                    markeredgecolor="#ff6b6b", markeredgewidth=2.5,
                    alpha=0.9, zorder=10)
            ax.plot(cx, cy, "o",
                    markersize=32, markerfacecolor="none",
                    markeredgecolor="#ff6b6b", markeredgewidth=1.0,
                    alpha=0.4, zorder=9)

        image_b64 = _generate_pinhole_image(
            direction=direction,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=25.0,
            extra_draw=_add_highlight,
        )

        all_names = [n for h, n in named_stars.items() if h != correct_hip]
        distractors = random.sample(all_names, min(3, len(all_names)))
        options = _shuffle_options(correct_name, *distractors)

        hint = "Эта звезда находится точно в центре изображения, отмечена красным кольцом"
        fun_fact = STAR_FACTS.get(correct_name, f"{correct_name} — яркая именная звезда (HIP {correct_hip}).")

        question = {
            "type": "star",
            "image": image_b64,
            "question": "Как называется выделенная красным кольцом звезда?",
            "options": options,
            "correct": correct_name,
            "hint": hint,
            "fun_fact": fun_fact,
        }
        session.current_question = question
        return question

    # ------------------------------------------------------------------
    # Mode 3 — Identify the Messier Object
    # ------------------------------------------------------------------
    def make_messier_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        mc = _get_messier_catalog()
        all_objects = mc.get_all_objects()

        available = [o for o in all_objects if int(o["m_number"]) not in session.used_objects]
        if not available:
            session.used_objects.clear()
            available = list(all_objects)

        obj = random.choice(available)
        m_num = int(obj["m_number"])
        session.used_objects.add(m_num)

        # ECI direction from pre-computed x, y, z fields in MessierCatalog
        direction = np.array(
            [float(obj["x"]), float(obj["y"]), float(obj["z"])],
            dtype=np.float64,
        )

        TYPE_NAMES = {
            1: "Галактика",
            2: "Шаровое скопление",
            3: "Рассеянное скопление",
            4: "Туманность",
            5: "Остаток сверхновой",
            6: "Звёздное облако",
        }
        obj_type_name = TYPE_NAMES.get(int(obj["obj_type"]), "Объект")
        obj_catalog_name = str(obj["name"]).strip()

        question_text = (
            f"Объект типа «{obj_type_name}» в созвездии {obj['constellation']}. "
            f"Что это за объект Мессье?"
        )

        other_nums = [int(o["m_number"]) for o in all_objects if int(o["m_number"]) != m_num]
        dist_nums = random.sample(other_nums, min(3, len(other_nums)))
        correct_label = f"M{m_num}"
        options = _shuffle_options(correct_label, *[f"M{n}" for n in dist_nums])

        def _add_object_marker(fig, ax, camera_cfg):
            cx = camera_cfg.width / 2
            cy = camera_cfg.height / 2
            marker_size = max(30, min(300, float(obj["size"]) * 3))
            ax.scatter(cx, cy, s=marker_size, marker="o",
                       facecolors="none", edgecolors="#4fc3f7",
                       linewidths=2, alpha=0.85, zorder=10)
            ax.scatter(cx, cy, s=12, marker=".", c="#4fc3f7", alpha=0.9, zorder=11)

        image_b64 = _generate_pinhole_image(
            direction=direction,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=50.0,
            extra_draw=_add_object_marker,
        )

        hint = f"Это {obj_type_name.lower()} с видимой звёздной величиной {float(obj['v_mag']):.1f}m"
        fun_fact = MESSIER_FACTS.get(m_num, f"M{m_num} — {obj_type_name} в созвездии {obj['constellation']}.")
        display_name = f"M{m_num}" + (f" — {obj_catalog_name}" if obj_catalog_name else "")

        question = {
            "type": "messier",
            "image": image_b64,
            "question": question_text,
            "options": options,
            "correct": correct_label,
            "hint": hint,
            "fun_fact": fun_fact,
            "object_name": display_name,
        }
        session.current_question = question
        return question

    # ------------------------------------------------------------------
    # Mode 4 — Draw the Constellation
    # ------------------------------------------------------------------
    def make_draw_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        pool = _get_constellation_list(session.difficulty)
        available = [c for c in pool if c not in session.used_objects]
        if not available:
            session.used_objects.clear()
            available = pool

        correct_abbr = random.choice(available)
        session.used_objects.add(correct_abbr)

        constellation_name = CONSTELLATIONS_DATA[correct_abbr]["name"]
        center = np.array(CONSTELLATIONS_DATA[correct_abbr]["center"], dtype=np.float64)
        lines = get_constellation_lines(correct_abbr)

        all_hip_ids: Set[int] = set()
        for line in lines:
            all_hip_ids.update(line)

        catalog = _get_catalog()
        projected = _gnomonic_project(all_hip_ids, center, catalog, magnitude)

        if len(projected) < 2:
            session.used_objects.discard(correct_abbr)
            return self.make_draw_question(session)

        xs = [v["x"] for v in projected.values()]
        ys = [v["y"] for v in projected.values()]
        max_r = max(max(abs(x) for x in xs), max(abs(y) for y in ys), 1e-9)

        named = _load_named_stars()
        stars_list = []
        for hip_id, v in projected.items():
            stars_list.append({
                "hip_id": hip_id,
                "x": round(v["x"] / max_r, 4),
                "y": round(v["y"] / max_r, 4),
                "v_mag": round(v["v_mag"], 2),
                "name": named.get(hip_id, ""),
            })

        ref_edges: List[List[int]] = []
        for line in lines:
            for i in range(len(line) - 1):
                a, b = int(line[i]), int(line[i + 1])
                if a in projected and b in projected:
                    ref_edges.append([a, b])

        fun_fact = CONSTELLATION_FACTS.get(correct_abbr, f"Созвездие {constellation_name}.")
        hint = f"У этого созвездия {len(all_hip_ids)} ключевых звёзд в рисунке"

        question = {
            "type": "draw",
            "question": "Соедините звёзды линиями так, как они соединены в рисунке созвездия.",
            "stars": stars_list,
            "ref_edges": ref_edges,
            "correct": constellation_name,
            "correct_abbr": correct_abbr,
            "hint": hint,
            "fun_fact": fun_fact,
        }
        session.current_question = question
        return question

    def check_draw_answer(self, session, drawn_edges: List[List[int]]) -> Dict[str, Any]:
        if not session.current_question or session.current_question["type"] != "draw":
            return {"error": "No active draw question"}

        ref = session.current_question["ref_edges"]
        ref_set = {(min(a, b), max(a, b)) for a, b in ref}
        drawn_set = {(min(a, b), max(a, b)) for a, b in drawn_edges}

        correct_edges = len(ref_set & drawn_set)
        total_ref = len(ref_set)
        score_pct = correct_edges / total_ref * 100 if total_ref else 0
        passed = score_pct >= 50.0

        return {
            "correct": passed,
            "score_pct": round(score_pct, 1),
            "correct_edges": correct_edges,
            "total_ref_edges": total_ref,
            "correct_answer": session.current_question["correct"],
            "ref_edges": ref,
            "fun_fact": session.current_question["fun_fact"],
        }

    # ------------------------------------------------------------------
    # Mode 5 — Constellation Trivia + Map
    # ------------------------------------------------------------------
    def make_trivia_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        pool = _get_constellation_list(session.difficulty)
        pool_set = set(pool)

        available_trivia = [
            q for q in TRIVIA_QUESTIONS
            if q["answer"] in pool_set and q["answer"] not in session.used_objects
        ]
        if not available_trivia:
            session.used_objects.clear()
            available_trivia = [q for q in TRIVIA_QUESTIONS if q["answer"] in pool_set]
        if not available_trivia:
            available_trivia = list(TRIVIA_QUESTIONS)

        trivia = random.choice(available_trivia)
        correct_abbr = trivia["answer"]
        session.used_objects.add(correct_abbr)

        correct_name = CONSTELLATIONS_DATA.get(correct_abbr, {}).get("name", correct_abbr)

        distractors = _random_distractors(correct_abbr, pool)
        dist_names = [CONSTELLATIONS_DATA[d]["name"] for d in distractors]
        options = _shuffle_options(correct_name, *dist_names)

        center = CONSTELLATIONS_DATA[correct_abbr]["center"]
        image_b64 = _generate_pinhole_image(
            direction=center,
            magnitude=magnitude,
            show_const=True,
            show_names=True,
            fov=110.0,
        )

        fun_fact = CONSTELLATION_FACTS.get(correct_abbr, f"Созвездие {correct_name}.")

        question = {
            "type": "trivia",
            "image": image_b64,
            "question": trivia["question"],
            "options": options,
            "correct": correct_name,
            "hint": trivia.get("hint", ""),
            "fun_fact": fun_fact,
        }
        session.current_question = question
        return question