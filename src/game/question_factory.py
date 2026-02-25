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
import math
import random
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from threading import Lock

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
# Close any figures that matplotlib may have created during import
plt.close("all")

from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.messier.messier_catalog import MessierCatalog, MessierType
from src.pinhole_projection.pinhole_projector import (
    CameraConfig, ShotConditions, PinholeConfig, Pinhole, ConstellationConfig,
)
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.constellations_metadata.constellations_data import (
    CONSTELLATIONS_DATA,
    get_constellation_lines,
    get_available_constellations,
)
from src.game.session import DIFFICULTY_CONSTELLATIONS, DIFFICULTY_MAGNITUDE

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parents[2]
_HIP_CATALOG: Optional[Catalog] = None
_PLANET_CATALOG: Optional[PlanetCatalog] = None
_MESSIER_CATALOG: Optional[MessierCatalog] = None
_catalog_lock = Lock()
_NAMED_STARS: Dict[int, str] = {}

OBS_TIME = datetime(2004, 6, 14, 6, 10, 0)

# ---------------------------------------------------------------------------
# Fallback named-star list (used when lines_data.json is unavailable/broken)
# HIP ID → English name for the brightest, most recognisable named stars
# ---------------------------------------------------------------------------
_FALLBACK_NAMED_STARS: Dict[int, str] = {
    32349:  "Sirius",
    91262:  "Vega",
    69673:  "Arcturus",
    37279:  "Procyon",
    24436:  "Rigel",
    27989:  "Betelgeuse",
    30438:  "Canopus",
    24608:  "Capella",
    97649:  "Altair",
    102098: "Deneb",
    80763:  "Antares",
    65474:  "Spica",
    49669:  "Regulus",
    11767:  "Polaris",
    21421:  "Aldebaran",
    677:    "Alpheratz",
    25336:  "Bellatrix",
    36850:  "Castor",
    37826:  "Pollux",
    57632:  "Denebola",
    54061:  "Dubhe",
    53910:  "Merak",
    65378:  "Mizar",
    3179:   "Schedar",
    746:    "Caph",
    6686:   "Ruchbah",
    5447:   "Mirach",
    113881: "Scheat",
    113963: "Markab",
    68702:  "Hadar",
    71683:  "Rigil Centaurus",
    60718:  "Acrux",
    87833:  "Eltanin",
    92420:  "Sheliak",
    93194:  "Sulafat",
    84345:  "Rasalgethi",
    80816:  "Kornephoros",
    77070:  "Unukalhai",
    72622:  "Zubenelgenubi",
    74785:  "Zubeneschamali",
    85670:  "Rastaban",
    75097:  "Pherkad",
    72105:  "Izar",
    68756:  "Thuban",
    95947:  "Albireo",
    100453: "Sadr",
    105199: "Alderamin",
    84012:  "Sabik",
    86228:  "Sargas",
    78820:  "Acrab",
    85696:  "Lesath",
    81266:  "Shaula",
    92855:  "Nunki",
    14135:  "Menkar",
    10826:  "Mira",
    20205:  "Aldebaran",
}

# ---------------------------------------------------------------------------
# Fun-facts
# ---------------------------------------------------------------------------
CONSTELLATION_FACTS: Dict[str, str] = {
    "ORI": "Орион содержит две из самых ярких звёзд неба — красный гигант Бетельгейзе и голубой сверхгигант Ригель.",
    "UMA": "Большая Медведица содержит Большой Ковш — один из самых узнаваемых астеризмов северного неба.",
    "CAS": "Кассиопея имеет форму буквы W или M и никогда не заходит за горизонт для жителей средних широт.",
    "CYG": "Лебедь содержит яркую звезду Денеб — одну из самых далёких и светлых звёзд Летнего треугольника.",
    "LEO": "Лев — зодиакальное созвездие, в котором находится галактика M66 из триплета Льва.",
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
    "Canopus":    "Канопус — вторая по яркости звезда неба, голубовато-белый сверхгигант на расстоянии 310 св. лет.",
    "Rigil Kentaurus": "Альфа Центавра — ближайшая к нам звёздная система (4,37 св. лет); тройная звезда.",
    "Acrux":      "Акрукс — ярчайшая звезда Южного Креста, голубой гигант на расстоянии 320 св. лет.",
    "Denebola":   "Денебола — «хвост Льва»; умеренно горячая белая звезда главной последовательности.",
    "Castor":     "Кастор — шестикратная звёздная система: три пары, вращающихся вокруг общего центра масс.",
    "Mizar":      "Мицар — первая двойная звезда, обнаруженная в телескоп (1617 г.); компонент — Алькор.",
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
    {"question": "Это созвездие содержит красного сверхгиганта Бетельгейзе и голубого сверхгиганта Ригель. В нём находится туманность M42.", "answer": "ORI", "hint": "Его пояс из трёх звёзд хорошо виден зимой"},
    {"question": "Созвездие с семью яркими звёздами, образующими «Большой Ковш». Две крайние звезды «указывают» на Полярную.", "answer": "UMA", "hint": "Медведица с длинным хвостом"},
    {"question": "Созвездие Летнего треугольника, в котором находится Вега — пятая по яркости звезда неба.", "answer": "LYR", "hint": "Музыкальный инструмент"},
    {"question": "Созвездие-«W», никогда не заходящее за горизонт в северных широтах. Названо в честь эфиопской царицы.", "answer": "CAS", "hint": "Гордая царица, посаженная на трон вверх ногами"},
    {"question": "В этом зодиакальном созвездии находится Антарес — «соперник Марса», самая красная из ярких звёзд.", "answer": "SCO", "hint": "Ядовитое членистоногое"},
    {"question": "Созвездие, в котором находится Альтаир — самый быстро вращающийся из ярких звёзд неба.", "answer": "AQL", "hint": "Гордая птица-символ США"},
    {"question": "Ближайшая к нам крупная галактика M31 находится именно в этом созвездии. Осенью видна невооружённым глазом.", "answer": "AND", "hint": "Мифологическая принцесса, прикованная к скале"},
    {"question": "В этом созвездии сконцентрировано наибольшее число объектов Мессье; оно указывает на центр Галактики.", "answer": "SGR", "hint": "Полуконь-получеловек с луком"},
    {"question": "Созвездие с ярчайшей звездой северного полушария — Арктуром. Выглядит как «воздушный змей».", "answer": "BOO", "hint": "Пастух медведей"},
    {"question": "Созвездие, в котором находится Денеб — одна из самых далёких светоносных звёзд, видимых невооружённым глазом.", "answer": "CYG", "hint": "Белая водоплавающая птица"},
]


# ---------------------------------------------------------------------------
# Singleton accessors
# ---------------------------------------------------------------------------
def _get_catalog() -> Catalog:
    global _HIP_CATALOG
    if _HIP_CATALOG is None:
        with _catalog_lock:
            if _HIP_CATALOG is None:
                _HIP_CATALOG = Catalog(
                    catalog_name=str(_BASE_DIR / "src" / "hip_catalog" / "hip_data.tsv"),
                    use_cache=True,
                )
                # Прогреть кэш сразу, чтобы первый запрос не был медленным
                _HIP_CATALOG.get_stars(CatalogConstraints(max_magnitude=6.5))
    return _HIP_CATALOG


def _get_planet_catalog() -> PlanetCatalog:
    global _PLANET_CATALOG
    if _PLANET_CATALOG is None:
        with _catalog_lock:
            if _PLANET_CATALOG is None:
                _PLANET_CATALOG = PlanetCatalog()
    return _PLANET_CATALOG


def _get_messier_catalog() -> MessierCatalog:
    global _MESSIER_CATALOG
    if _MESSIER_CATALOG is None:
        with _catalog_lock:
            if _MESSIER_CATALOG is None:
                _MESSIER_CATALOG = MessierCatalog()
    return _MESSIER_CATALOG


def _load_named_stars() -> Dict[int, str]:
    """
    Load named stars from lines_data.json.

    The file has a mixed structure — it may be a dict whose values include
    arrays of boundary strings, constellation-line objects, AND named-star
    entries keyed as "HIP XXXXX".  We iterate defensively: each key/value
    pair is processed individually so a single bad entry never aborts the
    whole load.

    If the file is completely unreadable, or no HIP entries are found, the
    built-in _FALLBACK_NAMED_STARS list is returned so the star-game always
    has a working pool of stars.
    """
    global _NAMED_STARS
    if _NAMED_STARS:
        return _NAMED_STARS

    lines_path = _BASE_DIR / "src" / "constellations_metadata" / "lines_data.json"
    parsed: Dict[int, str] = {}

    try:
        with open(lines_path, encoding="utf-8") as f:
            raw = json.load(f)

        # Handle top-level dict  (expected format)
        if isinstance(raw, dict):
            for key, value in raw.items():
                if not isinstance(key, str) or not key.startswith("HIP "):
                    continue
                try:
                    hip_id = int(key.split()[1])
                    if isinstance(value, list) and value:
                        entry = value[0]
                        name = (
                            entry.get("english")
                            or entry.get("native")
                            if isinstance(entry, dict) else None
                        )
                        if name:
                            parsed[hip_id] = str(name)
                except Exception:
                    continue  # skip this one entry, keep going

        # Handle top-level list  (rare alternative format)
        elif isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                for key, value in item.items():
                    if not isinstance(key, str) or not key.startswith("HIP "):
                        continue
                    try:
                        hip_id = int(key.split()[1])
                        if isinstance(value, list) and value:
                            entry = value[0]
                            name = (
                                entry.get("english")
                                or entry.get("native")
                                if isinstance(entry, dict) else None
                            )
                            if name:
                                parsed[hip_id] = str(name)
                    except Exception:
                        continue

    except Exception:
        pass  # file missing or JSON invalid — fall through to fallback

    # Merge: fallback first (lower priority), parsed data overrides
    _NAMED_STARS = {**_FALLBACK_NAMED_STARS, **parsed}
    return _NAMED_STARS


def _fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


# ---------------------------------------------------------------------------
# Core render helper
# ---------------------------------------------------------------------------
def _generate_pinhole_image(
    direction,
    magnitude: float,
    show_const: bool = True,
    show_names: bool = False,
    fov: float = 60.0,
    extra_draw=None,       # callable(fig, ax, camera_cfg)
) -> str:
    """Render a pinhole projection → base64 PNG."""
    plt.close("all")

    direction = np.asarray(direction, dtype=np.float32)
    norm = float(np.linalg.norm(direction))
    if norm > 0:
        direction = direction / norm

    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov,
        aspect_ratio=1.5,
        height_pix=600,
    )

    shot_cond = ShotConditions(
        center_direction=direction,
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

    constellation_config = ConstellationConfig(
        constellation_color="lightgray",
        constellation_linewidth=0.8,
        constellation_alpha=0.6,
    ) if show_const else None

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

    ax.set_aspect("equal")

    if extra_draw is not None:
        extra_draw(fig, ax, camera_cfg)

    return _fig_to_base64(fig)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------
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
    all_stars_data,
) -> Dict[int, Dict[str, float]]:
    """Project stars onto the tangent plane at `center`."""
    z = center / np.linalg.norm(center)
    arb = np.array([0.0, 0.0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x_ax = np.cross(arb, z); x_ax /= np.linalg.norm(x_ax)
    y_ax = np.cross(z, x_ax)

    hip_map = {int(s["hip_id"]): s for s in all_stars_data}
    result: Dict[int, Dict[str, float]] = {}
    for hip_id in hip_ids:
        s = hip_map.get(hip_id)
        if s is None:
            continue
        d = np.array([float(s["x"]), float(s["y"]), float(s["z"])])
        cos_t = float(np.dot(d, z))
        if cos_t < 0.05:
            continue
        result[hip_id] = {
            "hip_id": hip_id,
            "x": float(np.dot(d, x_ax) / cos_t),
            "y": float(np.dot(d, y_ax) / cos_t),
            "v_mag": float(s["v_mag"]),
        }
    return result


# ---------------------------------------------------------------------------
# QuestionFactory
# ---------------------------------------------------------------------------
class QuestionFactory:

    # ── Mode 1: Guess the Constellation ────────────────────────────────────
    def make_constellation_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        pool = _get_constellation_list(session.difficulty)
        available = [c for c in pool if c not in session.used_objects]
        if not available:
            session.used_objects.clear()
            available = pool[:]

        correct_abbr = random.choice(available)
        session.used_objects.add(correct_abbr)

        correct_name = CONSTELLATIONS_DATA[correct_abbr]["name"]
        center = CONSTELLATIONS_DATA[correct_abbr]["center"]

        image_b64 = _generate_pinhole_image(
            direction=center,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=60.0,
        )

        distractors = _random_distractors(correct_abbr, pool)
        options = _shuffle_options(correct_name,
                                   *[CONSTELLATIONS_DATA[d]["name"] for d in distractors])

        question = {
            "type": "constellation",
            "image": image_b64,
            "question": "Какое созвездие изображено на снимке?",
            "options": options,
            "correct": correct_name,
            "hint": f"Аббревиатура этого созвездия: {correct_abbr}",
            "fun_fact": CONSTELLATION_FACTS.get(correct_abbr, f"Созвездие {correct_name}."),
        }
        session.current_question = question
        return question

    # ── Mode 2: Name the Star ──────────────────────────────────────────────
    def make_star_question(self, session) -> Dict[str, Any]:
        """
        Show a pinhole image with the target star highlighted by a red ring
        and crosshair at the image centre.  The answer mode depends on
        session.difficulty:
          easy   — choose from 4 option buttons
          medium — type the star name
          hard   — type the star name + RA/Dec (±10° tolerance)
        """
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        named_stars = _load_named_stars()   # always non-empty thanks to fallback

        catalog = _get_catalog()
        constraints = CatalogConstraints(max_magnitude=magnitude)
        stars_data = catalog.get_stars(constraints)
        available_hip = set(int(s["hip_id"]) for s in stars_data)

        # Select candidate star
        candidates = {
            hip: name for hip, name in named_stars.items()
            if hip in available_hip and hip not in session.used_objects
        }
        if not candidates:
            session.used_objects.clear()
            candidates = {hip: name for hip, name in named_stars.items()
                          if hip in available_hip}
        if not candidates:
            # Widen magnitude limit to 7 — should always capture top named stars
            wide = catalog.get_stars(CatalogConstraints(max_magnitude=7.0))
            available_hip = set(int(s["hip_id"]) for s in wide)
            stars_data = wide
            candidates = {hip: name for hip, name in named_stars.items()
                          if hip in available_hip}
        if not candidates:
            # Absolute last resort: use the first star in the catalog
            star_arr = stars_data[0]
            correct_hip = int(star_arr["hip_id"])
            correct_name = named_stars.get(correct_hip, f"HIP {correct_hip}")
            candidates = {correct_hip: correct_name}

        correct_hip = random.choice(list(candidates.keys()))
        correct_name = candidates[correct_hip]
        session.used_objects.add(correct_hip)

        # Find star's catalog entry
        star_arr = next((s for s in stars_data if int(s["hip_id"]) == correct_hip), None)
        if star_arr is None:
            wide = catalog.get_stars(CatalogConstraints(max_magnitude=7.0))
            star_arr = next((s for s in wide if int(s["hip_id"]) == correct_hip), None)
        if star_arr is None:
            star_arr = stars_data[0]
            correct_hip = int(star_arr["hip_id"])
            correct_name = named_stars.get(correct_hip, f"HIP {correct_hip}")

        direction = np.array(
            [float(star_arr["x"]), float(star_arr["y"]), float(star_arr["z"])],
            dtype=np.float32,
        )

        # RA/Dec in degrees (stored server-side only, used for hard-mode validation)
        correct_ra_deg  = math.degrees(float(star_arr["ra"])) % 360.0
        correct_dec_deg = math.degrees(float(star_arr["dec"]))

        # Draw red ring + crosshair at image centre
        def _add_ring(fig, ax, camera_cfg):
            cx = camera_cfg.width  / 2
            cy = camera_cfg.height / 2
            # Main ring
            ax.plot(cx, cy, "o", markersize=24, markerfacecolor="none",
                    markeredgecolor="#ff6b6b", markeredgewidth=2.5,
                    alpha=0.9, zorder=10)

        image_b64 = _generate_pinhole_image(
            direction=direction,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=60,
            extra_draw=_add_ring,
        )

        # Option buttons (used in easy mode; generated for all modes for completeness)
        all_names = [n for h, n in named_stars.items() if h != correct_hip]
        distractors = random.sample(all_names, min(3, len(all_names)))
        options = _shuffle_options(correct_name, *distractors)

        # Difficulty-aware question text and hint
        difficulty = getattr(session, "difficulty", "easy")
        if difficulty == "easy":
            question_text = "Как называется звезда, отмеченная красным кольцом?"
            hint_text = ("Звезда находится точно в центре изображения, "
                         "отмечена красным кольцом и перекрестием")
        elif difficulty == "medium":
            question_text = "Введите название звезды, отмеченной красным кольцом"
            hint_text = (
                f"Название этой звезды состоит из {len(correct_name)} символов "
                f"и начинается на «{correct_name[0]}»"
            )
        else:  # hard
            question_text = (
                "Введите название звезды и её экваториальные координаты "
                "с точностью до ±10°"
            )
            ra_h = correct_ra_deg / 15.0
            hint_text = (
                f"RA ≈ {correct_ra_deg:.0f}° ({ra_h:.1f}ч), "
                f"Dec ≈ {correct_dec_deg:.0f}°"
            )

        question = {
            "type": "star",
            "image": image_b64,
            "question": question_text,
            "options": options,
            "correct": correct_name,
            # Server-side only — not sent to client in api_question response:
            "correct_ra_deg":  correct_ra_deg,
            "correct_dec_deg": correct_dec_deg,
            "hint": hint_text,
            "fun_fact": STAR_FACTS.get(
                correct_name,
                f"{correct_name} — именная звезда каталога Hipparcos (HIP {correct_hip})."
            ),
        }
        session.current_question = question
        return question

    # ── Mode 3: Messier Object ──────────────────────────────────────────────
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

        direction = np.array(
            [float(obj["x"]), float(obj["y"]), float(obj["z"])], dtype=np.float32
        )

        TYPE_NAMES = {1: "Галактика", 2: "Шаровое скопление", 3: "Рассеянное скопление",
                      4: "Туманность", 5: "Остаток сверхновой", 6: "Звёздное облако"}
        obj_type_name = TYPE_NAMES.get(int(obj["obj_type"]), "Объект")

        def _add_marker(fig, ax, camera_cfg):
            cx = camera_cfg.width  / 2
            cy = camera_cfg.height / 2
            ms = max(30, min(300, float(obj["size"]) * 3))
            color = mc.get_type_color(MessierType(obj["obj_type"]))
            ax.scatter(cx, cy, s=ms, marker="o", facecolors="none",
                       edgecolors=color, linewidths=2.5, alpha=0.9, zorder=10)
            ax.scatter(cx, cy, s=15, marker=".", c=color, alpha=1.0, zorder=11)
            ax.set_title(
                f"Тип: {obj_type_name}  |  Зв. вел.: {float(obj['v_mag']):.1f}  "
                f"|  Угл. р-р: {float(obj['size']):.1f}'",
                color="white", fontsize=9, pad=6,
            )

        image_b64 = _generate_pinhole_image(
            direction=direction,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=60.0,
            extra_draw=_add_marker,
        )

        obj_catalog_name = str(obj["name"]).strip()
        correct_label = f"M{m_num}"
        other_nums = [int(o["m_number"]) for o in all_objects if int(o["m_number"]) != m_num]
        options = _shuffle_options(
            correct_label,
            *[f"M{n}" for n in random.sample(other_nums, min(3, len(other_nums)))]
        )

        question = {
            "type": "messier",
            "image": image_b64,
            "question": f"Объект типа «{obj_type_name}» в созвездии {obj['constellation']}. Что это за объект Мессье?",
            "options": options,
            "correct": correct_label,
            "hint": f"Это {obj_type_name.lower()} с видимой звёздной величиной {float(obj['v_mag']):.1f}m",
            "fun_fact": MESSIER_FACTS.get(m_num, f"M{m_num} — {obj_type_name} в созвездии {obj['constellation']}."),
            "object_name": correct_label + (f" — {obj_catalog_name}" if obj_catalog_name else ""),
        }
        session.current_question = question
        return question

    # ── Mode 4: Draw the Constellation ─────────────────────────────────────
    def make_draw_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        bg_magnitude = min(magnitude + 1.0, 6.5)

        pool = _get_constellation_list(session.difficulty)
        available = [c for c in pool if c not in session.used_objects]
        if not available:
            session.used_objects.clear()
            available = pool[:]

        correct_abbr = random.choice(available)
        session.used_objects.add(correct_abbr)

        constellation_name = CONSTELLATIONS_DATA[correct_abbr]["name"]
        center = np.array(CONSTELLATIONS_DATA[correct_abbr]["center"], dtype=np.float64)
        lines = get_constellation_lines(correct_abbr)

        const_hip_ids: Set[int] = set()
        for line in lines:
            const_hip_ids.update(line)

        catalog = _get_catalog()
        bg_constraints = CatalogConstraints(max_magnitude=bg_magnitude)
        all_stars_data = catalog.get_stars(bg_constraints)

        const_projected = _gnomonic_project(const_hip_ids, center, all_stars_data)

        if len(const_projected) < 2:
            session.used_objects.discard(correct_abbr)
            return self.make_draw_question(session)

        z = center / np.linalg.norm(center)
        bg_projected: Dict[int, Dict[str, float]] = {}
        for s in all_stars_data:
            hip_id = int(s["hip_id"])
            if hip_id in const_hip_ids:
                continue
            d = np.array([float(s["x"]), float(s["y"]), float(s["z"])])
            cos_t = float(np.dot(d, z))
            if cos_t < 0.7:
                continue
            arb = np.array([0.0, 0.0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
            x_ax = np.cross(arb, z); x_ax /= np.linalg.norm(x_ax)
            y_ax = np.cross(z, x_ax)
            px = float(np.dot(d, x_ax) / cos_t)
            py = float(np.dot(d, y_ax) / cos_t)
            bg_projected[hip_id] = {"hip_id": hip_id, "x": px, "y": py, "v_mag": float(s["v_mag"])}

        all_xs = [v["x"] for v in const_projected.values()]
        all_ys = [v["y"] for v in const_projected.values()]
        max_r = max(max(abs(x) for x in all_xs), max(abs(y) for y in all_ys), 1e-9)
        max_r *= 1.2

        named = _load_named_stars()

        stars_list = []
        for hip_id, v in const_projected.items():
            stars_list.append({
                "hip_id": hip_id,
                "x": round(v["x"] / max_r, 4),
                "y": round(v["y"] / max_r, 4),
                "v_mag": round(v["v_mag"], 2),
                "name": named.get(hip_id, ""),
                "is_constellation": True,
            })

        for hip_id, v in bg_projected.items():
            nx = v["x"] / max_r
            ny = v["y"] / max_r
            if abs(nx) > 1.4 or abs(ny) > 1.4:
                continue
            stars_list.append({
                "hip_id": hip_id,
                "x": round(nx, 4),
                "y": round(ny, 4),
                "v_mag": round(v["v_mag"], 2),
                "name": "",
                "is_constellation": False,
            })

        ref_edges: List[List[int]] = []
        for line in lines:
            for i in range(len(line) - 1):
                a, b = int(line[i]), int(line[i + 1])
                if a in const_projected and b in const_projected:
                    ref_edges.append([a, b])

        question = {
            "type": "draw",
            "question": "Соедините звёзды созвездия линиями так, как они соединены на официальных картах.",
            "stars": stars_list,
            "ref_edges": ref_edges,
            "correct": constellation_name,
            "correct_abbr": correct_abbr,
            "hint": f"В рисунке этого созвездия {len(ref_edges)} линий",
            "fun_fact": CONSTELLATION_FACTS.get(correct_abbr, f"Созвездие {constellation_name}."),
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

    # ── Mode 5: Trivia ──────────────────────────────────────────────────────
    def make_trivia_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        pool = _get_constellation_list(session.difficulty)
        pool_set = set(pool)

        available_trivia = [q for q in TRIVIA_QUESTIONS
                            if q["answer"] in pool_set and q["answer"] not in session.used_objects]
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
        options = _shuffle_options(correct_name,
                                   *[CONSTELLATIONS_DATA[d]["name"] for d in distractors])

        center = CONSTELLATIONS_DATA[correct_abbr]["center"]
        image_b64 = _generate_pinhole_image(
            direction=center,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=110.0,
        )

        question = {
            "type": "trivia",
            "image": image_b64,
            "question": trivia["question"],
            "options": options,
            "correct": correct_name,
            "hint": trivia.get("hint", ""),
            "fun_fact": CONSTELLATION_FACTS.get(correct_abbr, f"Созвездие {correct_name}."),
        }
        session.current_question = question
        return question