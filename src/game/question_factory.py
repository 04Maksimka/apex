"""
Question factory for all 5 AstraGeek Sky Quiz game modes.

Modes:
  1. constellation — Guess the constellation from a pinhole image (no labels)
  2. star          — Name the highlighted bright star
  3. messier       — Identify the Messier deep-sky object
  4. draw          — Connect stars to draw the constellation
  5. trivia        — Answer trivia and find the described constellation
"""

from __future__ import annotations

import base64
import io
import json
import math
import random
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy._typing import NDArray

from src.constellations_metadata.constellations_data import (
    CONSTELLATIONS_DATA,
    get_available_constellations,
    get_constellation_lines,
)
from src.game.session import DIFFICULTY_CONSTELLATIONS, DIFFICULTY_MAGNITUDE
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

# Close any figures that matplotlib may have created during import
matplotlib.use("Agg")
plt.close("all")

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
# Fallback named-star list (used when index.json is unavailable/broken)
# HIP ID → English name for the brightest, most recognisable named stars
# ---------------------------------------------------------------------------
_FALLBACK_NAMED_STARS: Dict[int, str] = {
    32349: "Sirius",
    91262: "Vega",
    69673: "Arcturus",
    37279: "Procyon",
    24436: "Rigel",
    27989: "Betelgeuse",
    30438: "Canopus",
    24608: "Capella",
    97649: "Altair",
    102098: "Deneb",
    80763: "Antares",
    65474: "Spica",
    49669: "Regulus",
    11767: "Polaris",
    21421: "Aldebaran",
    677: "Alpheratz",
    25336: "Bellatrix",
    36850: "Castor",
    37826: "Pollux",
    57632: "Denebola",
    54061: "Dubhe",
    53910: "Merak",
    65378: "Mizar",
    3179: "Schedar",
    746: "Caph",
    6686: "Ruchbah",
    5447: "Mirach",
    113881: "Scheat",
    113963: "Markab",
    68702: "Hadar",
    71683: "Rigil Centaurus",
    60718: "Acrux",
    87833: "Eltanin",
    92420: "Sheliak",
    93194: "Sulafat",
    84345: "Rasalgethi",
    80816: "Kornephoros",
    77070: "Unukalhai",
    72622: "Zubenelgenubi",
    74785: "Zubeneschamali",
    85670: "Rastaban",
    75097: "Pherkad",
    72105: "Izar",
    68756: "Thuban",
    95947: "Albireo",
    100453: "Sadr",
    105199: "Alderamin",
    84012: "Sabik",
    86228: "Sargas",
    78820: "Acrab",
    85696: "Lesath",
    81266: "Shaula",
    92855: "Nunki",
    14135: "Menkar",
    10826: "Mira",
    20205: "Aldebaran",
}

# ---------------------------------------------------------------------------
# Fun-facts
# ---------------------------------------------------------------------------
CONSTELLATION_FACTS: Dict[str, str] = {
    "ORI": (
        "В Орионе есть две звезды первой величины: красный сверхгигант "
        "Бетельгейзе и голубой сверхгигант Ригель."
    ),
    "UMA": (
        "Большая Медведица включает Большой Ковш — самый известный "
        "астеризм северного неба."
    ),
    "CAS": (
        "Кассиопея похожа на W или M и для средних широт обычно "
        "циркумполярна, то есть не заходит за горизонт."
    ),
    "CYG": (
        "В Лебеде находится Денеб — очень яркая и при этом далёкая "
        "звезда, входящая в Летний треугольник."
    ),
    "LEO": (
        "Лев — зодиакальное созвездие; здесь расположена галактика M66 "
        "из триплета Льва."
    ),
    "SCO": (
        "Скорпион легко узнать по Антаресу: это красный сверхгигант, "
        "настолько большой, что «поместил бы» орбиту Марса."
    ),
    "GEM": (
        "Близнецы названы в честь Кастора и Поллукса — мифологических "
        "братьев, связанных с двумя яркими звёздами созвездия."
    ),
    "TAU": (
        "В Тельце находится M1 (Крабовидная туманность) — остаток "
        "сверхновой, наблюдавшейся в 1054 году."
    ),
    "AQL": (
        "В Орле находится Альтаир — одна из трёх звёзд Летнего "
        "треугольника и заметный ориентир летнего неба."
    ),
    "LYR": (
        "Лира содержит Вегу — 5‑ю по яркости звезду неба; около 12 000 "
        "лет назад она была близка к северному полюсу мира."
    ),
    "PER": (
        "В Персее находится Алголь («Демонская звезда») — яркая "
        "затменно‑переменная звезда с заметными падениями блеска."
    ),
    "AUR": (
        "В Возничем светит Капелла — 6‑я по яркости звезда неба; это "
        "не одиночная звезда, а многокомпонентная система."
    ),
    "VIR": (
        "Дева — крупнейшее зодиакальное созвездие; в этой области неба "
        "расположено Скопление Девы из ~1300 галактик."
    ),
    "SGR": (
        "Стрелец направлен в сторону центра Млечного Пути; в нём "
        "находится более 15 объектов каталога Мессье."
    ),
    "AND": (
        "В Андромеде находится M31 — ближайшая к нам крупная галактика, "
        "которую в хороших условиях видно невооружённым глазом."
    ),
    "BOO": (
        "В Волопасе сияет Арктур — ярчайшая звезда северного полушария "
        "и один из главных ориентиров весеннего неба."
    ),
    "HER": (
        "В Геркулесе находится M13 — Великое шаровое скопление, одно из "
        "самых эффектных объектов для небольшого телескопа."
    ),
    "DRA": (
        "Дракон окружает Малую Медведицу; около 5000 лет назад Тубан "
        "был звездой‑полюсом, близкой к северному полюсу мира."
    ),
    "CRU": (
        "Южный Крест — самое маленькое по площади созвездие и важный "
        "ориентир для навигации в южном полушарии."
    ),
    "UMI": (
        "В Малой Медведице находится Полярная звезда — примерно в 430 "
        "световых годах от нас и рядом с северным полюсом мира."
    ),
}


STAR_FACTS: Dict[str, str] = {
    "Sirius": (
        "Сириус — самая яркая звезда ночного неба (−1,46m); это двойная "
        "система на расстоянии 8,6 световых лет."
    ),
    "Vega": (
        "Вега — одна из вершин Летнего треугольника; около 14 000 лет "
        "назад она была Полярной звездой."
    ),
    "Arcturus": (
        "Арктур — ярчайшая звезда северного полушария; красный гигант "
        "примерно в 37 световых годах от нас."
    ),
    "Capella": (
        "Капелла — сложная система: два ярких компонента‑гиганта и ещё "
        "пара тусклых звёзд меньшей массы."
    ),
    "Rigel": (
        "Ригель — голубой сверхгигант; его светимость оценивают примерно "
        "в 120 000 раз выше солнечной."
    ),
    "Procyon": (
        "Процион — двойная система: яркий субгигант и белый карлик; "
        "расстояние около 11,5 световых лет."
    ),
    "Betelgeuse": (
        "Бетельгейзе — красный сверхгигант на поздней стадии эволюции; "
        "его диаметр больше орбиты Юпитера."
    ),
    "Altair": (
        "Альтаир вращается очень быстро (286 км/с), поэтому заметно "
        "сплюснут у экватора — примерно на 20%."
    ),
    "Aldebaran": (
        "Альдебаран — оранжевый гигант, «глаз» Тельца; находится примерно "
        "в 65 световых годах от Земли."
    ),
    "Spica": (
        "Спика — ярчайшая звезда Девы и тесная двойная система; обе "
        "звезды деформированы из‑за значительных приливных сил."
    ),
    "Antares": (
        "Антарес — «соперник Марса»; красный сверхгигант диаметром "
        "примерно ~700 солнечных."
    ),
    "Pollux": (
        "Поллукс — ярчайшая звезда Близнецов; у неё известна экзопланета "
        "Поллукс b."
    ),
    "Deneb": (
        "Денеб — один из самых далёких ярких объектов неба: около ~2600 "
        "световых лет и светимость 200 000 Солнц."
    ),
    "Regulus": (
        "Регул — «сердце Льва»; это быстро вращающаяся звезда, почти "
        "достигшая критической скорости распада."
    ),
    "Polaris": (
        "Полярная звезда находится примерно в 0,7° от полюса мира и "
        "медленно приближается к нему из‑за прецессии."
    ),
    "Canopus": (
        "Канопус — 2‑я по яркости звезда неба; голубовато‑белый "
        "сверхгигант примерно в 310 световых годах."
    ),
    "Rigil Kentaurus": (
        "Альфа Центавра — ближайшая к нам звёздная система (4,37 св. лет); "
        "это тройная звезда."
    ),
    "Acrux": (
        "Акрукс — ярчайшая звезда Южного Креста; голубой гигант примерно "
        "в 320 световых годах от нас."
    ),
    "Denebola": (
        "Денебола — «хвост Льва»; белая звезда главной последовательности "
        "умеренно высокой температуры."
    ),
    "Castor": (
        "Кастор — шестикратная звёздная система: три пары, которые "
        "вращаются вокруг общего центра масс."
    ),
    "Mizar": (
        "Мицар — первая двойная звезда, обнаруженная в телескоп (1617 г.); "
        "рядом заметен Алькор как визуальный компаньон."
    ),
}


MESSIER_FACTS: Dict[int, str] = {
    1: (
        "M1 (Крабовидная туманность) — остаток сверхновой 1054 года; "
        "в центре находится нейтронная звезда‑пульсар."
    ),
    31: (
        "M31 (Туманность Андромеды) — ближайшая крупная галактика; "
        "через ~4 млрд лет она сольётся с Млечным Путём."
    ),
    42: (
        "M42 (Туманность Ориона) — активная область звездообразования "
        "примерно в 1344 световых годах."
    ),
    45: (
        "M45 (Плеяды) — молодое рассеянное скопление; большинство звёзд "
        "образовалось около ~100 млн лет назад."
    ),
    13: (
        "M13 — Великое шаровое скопление Геркулеса: около 300 000 звёзд "
        "на расстоянии 22 200 световых лет."
    ),
    51: (
        "M51 (Галактика Водоворот) — первая галактика, у которой заметили "
        "спиральную структуру (1845 г.)."
    ),
    57: (
        "M57 (Кольцо Лиры) — планетарная туманность: умирающая звезда "
        "сбросила оболочку, и газ светится вокруг ядра."
    ),
    27: (
        "M27 (Гантель) — первая открытая планетарная туманность "
        "(Мессье, 1764)."
    ),
    8: (
        "M8 (Лагуна) — один из немногих объектов Мессье, "
        "которые можно увидеть невооружённым глазом."
    ),
}


TRIVIA_QUESTIONS: List[Dict[str, Any]] = [
    {
        "question": (
            "Созвездие с Бетельгейзе и Ригелем; здесь находится M42 — "
            "Туманность Ориона, яркая область звездообразования."
        ),
        "answer": "ORI",
        "hint": "Пояс из трёх звёзд, хорошо виден зимой",
    },
    {
        "question": (
            "Созвездие с «Большим Ковшом» из семи ярких звёзд; две крайние "
            "звезды на ковше указывают направление на Полярную."
        ),
        "answer": "UMA",
        "hint": "Медведица с длинным хвостом",
    },
    {
        "question": (
            "Созвездие Летнего треугольника, где находится Вега — пятая по "
            "яркости звезда ночного неба."
        ),
        "answer": "LYR",
        "hint": "Музыкальный инструмент",
    },
    {
        "question": (
            "Созвездие‑«W», которое в северных широтах обычно не заходит за "
            "горизонт. Названо в честь эфиопской царицы."
        ),
        "answer": "CAS",
        "hint": "Гордая царица",
    },
    {
        "question": (
            "В этом зодиакальном созвездии находится Антарес — «соперник "
            "Марса», одна из самых красных ярких звёзд."
        ),
        "answer": "SCO",
        "hint": "Ядовитое членистоногое",
    },
    {
        "question": (
            "Созвездие, где находится Альтаир — один из самых быстро "
            "вращающихся ярких объектов на небе."
        ),
        "answer": "AQL",
        "hint": "Гордая птица-символ США",
    },
    {
        "question": (
            "Ближайшая крупная галактика M31 находится в этом созвездии; "
            "осенью её можно увидеть невооружённым глазом."
        ),
        "answer": "AND",
        "hint": "Принцесса, прикованная к скале",
    },
    {
        "question": (
            "Созвездие с большим числом объектов Мессье; оно направлено "
            "примерно в сторону центра Млечного Пути."
        ),
        "answer": "SGR",
        "hint": "Полуконь-получеловек с луком",
    },
    {
        "question": (
            "Созвездие с Арктуром — ярчайшей звездой северного полушария; "
            "его фигуру часто сравнивают с «воздушным змеем»."
        ),
        "answer": "BOO",
        "hint": "Пастух",
    },
    {
        "question": (
            "Созвездие, где находится Денеб — один из самых далёких ярких "
            "объектов, видимых невооружённым глазом."
        ),
        "answer": "CYG",
        "hint": "Белая водоплавающая птица",
    },
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
                    catalog_name=str(
                        _BASE_DIR / "src" / "hip_catalog" / "hip_data.tsv"
                    ),
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
    Load named stars from index.json.

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

    lines_path = _BASE_DIR / "src" / "constellations_metadata" / "index.json"
    parsed: Dict[int, str] = {}

    try:
        with open(lines_path, encoding="utf-8") as f:
            raw = json.load(f)

        common_names = raw.get("common_names")
        if not isinstance(common_names, dict):
            raise SystemExit(
                "ERROR: index.json: expected key 'common_names' as dict"
            )

        # Handle top-level dict  (expected format)
        if isinstance(common_names, dict):
            for key, value in common_names.items():
                if not isinstance(key, str) or not key.startswith("HIP "):
                    continue
                try:
                    hip_id = int(key.split()[1])
                    if isinstance(value, list) and value:
                        entry = value[0]
                        name = (
                            entry.get("english") or entry.get("native")
                            if isinstance(entry, dict)
                            else None
                        )
                        if name:
                            parsed[hip_id] = str(name)
                except Exception:
                    continue  # skip this one entry, keep going

            print("Stars loaded from index.json")
    except Exception:
        # file missing or JSON invalid — fall through to fallback
        print("Stars loaded from data")

    # Merge: fallback first (lower priority), parsed data overrides
    _NAMED_STARS = {**_FALLBACK_NAMED_STARS, **parsed}
    return _NAMED_STARS


def _fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=100,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
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
    extra_draw=None,  # callable(fig, ax, camera_cfg)
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

    constellation_config = (
        ConstellationConfig(
            constellation_color="lightgray",
            constellation_linewidth=0.8,
            constellation_alpha=0.6,
        )
        if show_const
        else None
    )

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


def _random_distractors(
    correct: str, pool: List[str], n: int = 3
) -> List[str]:
    candidates = [c for c in pool if c != correct]
    return random.sample(candidates, min(n, len(candidates)))


def _shuffle_options(*items: str) -> List[str]:
    opts = list(items)
    random.shuffle(opts)
    return opts


def _gnomonic_project(
    hip_ids: Set[int],
    center: NDArray,
    all_stars_data,
) -> Dict[int, Dict[str, float]]:
    """Project stars onto the tangent plane at `center`."""
    z = center / np.linalg.norm(center)
    arb = (
        np.array([0.0, 0.0, 1.0])
        if abs(z[2]) < 0.9
        else np.array([1.0, 0.0, 0.0])
    )

    x_ax = np.cross(arb, z)
    x_ax /= np.linalg.norm(x_ax)
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
        options = _shuffle_options(
            correct_name,
            *[CONSTELLATIONS_DATA[d]["name"] for d in distractors],
        )

        question = {
            "type": "constellation",
            "image": image_b64,
            "question": "Какое созвездие изображено на снимке?",
            "options": options,
            "correct": correct_name,
            "hint": f"Аббревиатура этого созвездия: {correct_abbr}",
            "fun_fact": CONSTELLATION_FACTS.get(
                correct_abbr, f"Созвездие {correct_name}."
            ),
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
        named_stars = (
            _load_named_stars()
        )  # always non-empty thanks to fallback

        catalog = _get_catalog()
        constraints = CatalogConstraints(max_magnitude=magnitude)
        stars_data = catalog.get_stars(constraints)
        available_hip = set(int(s["hip_id"]) for s in stars_data)

        # Select candidate star
        candidates = {
            hip: name
            for hip, name in named_stars.items()
            if hip in available_hip and hip not in session.used_objects
        }
        if not candidates:
            session.used_objects.clear()
            candidates = {
                hip: name
                for hip, name in named_stars.items()
                if hip in available_hip
            }
        if not candidates:
            # Widen magnitude limit to 7 — should capture top named stars
            wide = catalog.get_stars(CatalogConstraints(max_magnitude=7.0))
            available_hip = set(int(s["hip_id"]) for s in wide)
            stars_data = wide
            candidates = {
                hip: name
                for hip, name in named_stars.items()
                if hip in available_hip
            }
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
        star_arr = next(
            (s for s in stars_data if int(s["hip_id"]) == correct_hip), None
        )
        if star_arr is None:
            wide = catalog.get_stars(CatalogConstraints(max_magnitude=7.0))
            star_arr = next(
                (s for s in wide if int(s["hip_id"]) == correct_hip), None
            )
        if star_arr is None:
            star_arr = stars_data[0]
            correct_hip = int(star_arr["hip_id"])
            correct_name = named_stars.get(correct_hip, f"HIP {correct_hip}")

        direction = np.array(
            [float(star_arr["x"]), float(star_arr["y"]), float(star_arr["z"])],
            dtype=np.float32,
        )

        # RA/Dec in degrees (stored server-side only, for hard-mode validation)
        correct_ra_deg = math.degrees(float(star_arr["ra"])) % 360.0
        correct_dec_deg = math.degrees(float(star_arr["dec"]))

        # Draw red ring + crosshair at image centre
        def _add_ring(fig, ax, camera_cfg):
            cx = camera_cfg.width / 2
            cy = camera_cfg.height / 2
            # Main ring
            ax.plot(
                cx,
                cy,
                "o",
                markersize=24,
                markerfacecolor="none",
                markeredgecolor="#ff6b6b",
                markeredgewidth=2.5,
                alpha=0.9,
                zorder=10,
            )

        image_b64 = _generate_pinhole_image(
            direction=direction,
            magnitude=magnitude,
            show_const=True,
            show_names=False,
            fov=60,
            extra_draw=_add_ring,
        )

        # Option buttons (used in easy mode; for all modes for completeness)
        all_names = [n for h, n in named_stars.items() if h != correct_hip]
        distractors = random.sample(all_names, min(3, len(all_names)))
        options = _shuffle_options(correct_name, *distractors)

        # Difficulty-aware question text and hint
        difficulty = getattr(session, "difficulty", "easy")
        if difficulty == "easy":
            question_text = "Как называется звезда, отмеченная красным?"
            hint_text = f"Это {correct_name}"
        elif difficulty == "medium":
            question_text = "Введите название звезды, отмеченной красным"
            hint_text = (
                f"Название этой звезды состоит из {len(correct_name)} символов"
                f" и начинается на «{correct_name[0]}»"
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
            "correct_ra_deg": correct_ra_deg,
            "correct_dec_deg": correct_dec_deg,
            "hint": hint_text,
            "fun_fact": STAR_FACTS.get(
                correct_name,
                f"{correct_name} — именная звезда каталога "
                f"Hipparcos (HIP {correct_hip}).",
            ),
        }
        session.current_question = question
        return question

    # ── Mode 3: Messier Object ──────────────────────────────────────────────
    def make_messier_question(self, session) -> Dict[str, Any]:
        magnitude = DIFFICULTY_MAGNITUDE[session.difficulty]
        mc = _get_messier_catalog()
        all_objects = mc.get_all_objects()

        available = [
            o
            for o in all_objects
            if int(o["m_number"]) not in session.used_objects
        ]
        if not available:
            session.used_objects.clear()
            available = list(all_objects)

        obj = random.choice(available)
        m_num = int(obj["m_number"])
        session.used_objects.add(m_num)

        direction = np.array(
            [float(obj["x"]), float(obj["y"]), float(obj["z"])],
            dtype=np.float32,
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

        def _add_marker(fig, ax, camera_cfg):
            cx = camera_cfg.width / 2
            cy = camera_cfg.height / 2
            ms = max(30, min(300, float(obj["size"]) * 3))
            color = mc.get_type_color(MessierType(obj["obj_type"]))
            ax.scatter(
                cx,
                cy,
                s=ms,
                marker="o",
                facecolors="none",
                edgecolors=color,
                linewidths=2.5,
                alpha=0.9,
                zorder=10,
            )
            ax.scatter(cx, cy, s=15, marker=".", c=color, alpha=1.0, zorder=11)
            ax.set_title(
                f"Тип: {obj_type_name}  |  Зв. вел.: {float(obj['v_mag']):.1f}"
                f"  |  Угл. р-р: {float(obj['size']):.1f}'",
                color="white",
                fontsize=9,
                pad=6,
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
        other_nums = [
            int(o["m_number"])
            for o in all_objects
            if int(o["m_number"]) != m_num
        ]
        options = _shuffle_options(
            correct_label,
            *[
                f"M{n}"
                for n in random.sample(other_nums, min(3, len(other_nums)))
            ],
        )

        question = {
            "type": "messier",
            "image": image_b64,
            "question": f"Объект типа «{obj_type_name}» в созвездии "
            f"{obj['constellation']}. Что это за объект Мессье?",
            "options": options,
            "correct": correct_label,
            "hint": f"Это {obj_type_name.lower()} с видимой "
            f"звёздной величиной {float(obj['v_mag']):.1f}m",
            "fun_fact": MESSIER_FACTS.get(
                m_num,
                f"M{m_num} — {obj_type_name} в созвездии "
                f"{obj['constellation']}.",
            ),
            "object_name": correct_label
            + (f" — {obj_catalog_name}" if obj_catalog_name else ""),
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
        center = np.array(
            CONSTELLATIONS_DATA[correct_abbr]["center"], dtype=np.float64
        )
        lines = get_constellation_lines(correct_abbr)

        const_hip_ids: Set[int] = set()
        for line in lines:
            const_hip_ids.update(line)

        catalog = _get_catalog()
        bg_constraints = CatalogConstraints(max_magnitude=bg_magnitude)
        all_stars_data = catalog.get_stars(bg_constraints)

        const_projected = _gnomonic_project(
            const_hip_ids, center, all_stars_data
        )

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
            arb = (
                np.array([0.0, 0.0, 1.0])
                if abs(z[2]) < 0.9
                else np.array([1.0, 0.0, 0.0])
            )
            x_ax = np.cross(arb, z)
            x_ax /= np.linalg.norm(x_ax)
            y_ax = np.cross(z, x_ax)
            px = float(np.dot(d, x_ax) / cos_t)
            py = float(np.dot(d, y_ax) / cos_t)
            bg_projected[hip_id] = {
                "hip_id": hip_id,
                "x": px,
                "y": py,
                "v_mag": float(s["v_mag"]),
            }

        all_xs = [v["x"] for v in const_projected.values()]
        all_ys = [v["y"] for v in const_projected.values()]
        max_r = max(
            max(abs(x) for x in all_xs), max(abs(y) for y in all_ys), 1e-9
        )
        max_r *= 1.2

        named = _load_named_stars()

        stars_list = []
        for hip_id, v in const_projected.items():
            stars_list.append(
                {
                    "hip_id": hip_id,
                    "x": round(v["x"] / max_r, 4),
                    "y": round(v["y"] / max_r, 4),
                    "v_mag": round(v["v_mag"], 2),
                    "name": named.get(hip_id, ""),
                    "is_constellation": True,
                }
            )

        for hip_id, v in bg_projected.items():
            nx = v["x"] / max_r
            ny = v["y"] / max_r
            if abs(nx) > 1.4 or abs(ny) > 1.4:
                continue
            stars_list.append(
                {
                    "hip_id": hip_id,
                    "x": round(nx, 4),
                    "y": round(ny, 4),
                    "v_mag": round(v["v_mag"], 2),
                    "name": "",
                    "is_constellation": False,
                }
            )

        ref_edges: List[List[int]] = []
        for line in lines:
            for i in range(len(line) - 1):
                a, b = int(line[i]), int(line[i + 1])
                if a in const_projected and b in const_projected:
                    ref_edges.append([a, b])

        question = {
            "type": "draw",
            "question": "Соедините звёзды созвездия линиями так, "
            "как они соединены на официальных картах.",
            "stars": stars_list,
            "ref_edges": ref_edges,
            "correct": constellation_name,
            "correct_abbr": correct_abbr,
            "hint": f"В рисунке этого созвездия {len(ref_edges)} линий",
            "fun_fact": CONSTELLATION_FACTS.get(
                correct_abbr, f"Созвездие {constellation_name}."
            ),
        }
        session.current_question = question
        return question

    def check_draw_answer(
        self, session, drawn_edges: List[List[int]]
    ) -> Dict[str, Any]:
        if (
            not session.current_question
            or session.current_question["type"] != "draw"
        ):
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

        available_trivia = [
            q
            for q in TRIVIA_QUESTIONS
            if q["answer"] in pool_set
            and q["answer"] not in session.used_objects
        ]
        if not available_trivia:
            session.used_objects.clear()
            available_trivia = [
                q for q in TRIVIA_QUESTIONS if q["answer"] in pool_set
            ]
        if not available_trivia:
            available_trivia = list(TRIVIA_QUESTIONS)

        trivia = random.choice(available_trivia)
        correct_abbr = trivia["answer"]
        session.used_objects.add(correct_abbr)

        correct_name = CONSTELLATIONS_DATA.get(correct_abbr, {}).get(
            "name", correct_abbr
        )
        distractors = _random_distractors(correct_abbr, pool)
        options = _shuffle_options(
            correct_name,
            *[CONSTELLATIONS_DATA[d]["name"] for d in distractors],
        )

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
            "fun_fact": CONSTELLATION_FACTS.get(
                correct_abbr, f"Созвездие {correct_name}."
            ),
        }
        session.current_question = question
        return question
