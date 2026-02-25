import os
import tempfile
import threading
import uuid
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
from flask import Flask, redirect, request, send_file

from src.constellations_metadata.constellations_data import (
    get_constellation_center,
)
from src.helpers.pdf_helpers.figure2pdf import (
    save_figure_pinhole,
    save_figure_skychart,
)
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.pinhole_projection.pinhole_projector import (
    CameraConfig,
    Pinhole,
    PinholeConfig,
    ShotConditions,
)
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.stereographic_projection.stereographic_projector import (
    ConstellationConfig,
    StereoProjConfig,
    StereoProjector,
)
from src.web.game_blueprint import game_bp
from src.web.messier_blueprint import messier_bp

matplotlib.use("Agg")

app = Flask(__name__, static_folder="public_html", static_url_path="")
app.register_blueprint(messier_bp)
app.register_blueprint(game_bp)

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
# BASE_DIR = корень проекта AstraGeek/

CATALOG = Catalog(
    catalog_name=os.path.join(BASE_DIR, "src", "hip_catalog", "hip_data.tsv"),
    use_cache=True,
)


# ── Прогрев каталогов при старте (чтобы первый игровой запрос не лагал) ──────
def _warmup_catalogs():
    """
    Загружаем все каталоги игры в фоновом потоке сразу после старта сервера.
    Это устраняет задержку 15–40 секунд при первом открытии игры,
    когда Hipparcos / Мессье / matplotlib ещё не инициализированы.
    """
    try:
        print("[warmup] Прогрев каталогов игры...")
        from src.game.question_factory import (
            _get_catalog,
            _get_messier_catalog,
            _get_named_stars,
        )

        _get_catalog()
        _get_messier_catalog()
        _get_named_stars()
        # Первый plt.subplots() всегда медленный — прогреваем заранее
        fig, _ax = plt.subplots()
        plt.close(fig)
        print("[warmup] Каталоги загружены ✓")
    except Exception as exc:
        print(f"[warmup] Предупреждение: не удалось прогреть каталоги: {exc}")


threading.Thread(target=_warmup_catalogs, daemon=True).start()


# ── Основные страницы ────────────────────────────────────────────────────────


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/generator")
def generator():
    return app.send_static_file("generator.html")


# ── Игры ─────────────────────────────────────────────────────────────────────


@app.route("/games")
def games_redirect():
    """Удобный алиас /games → /game/ (лобби игр)."""
    return redirect("/game/", code=301)


@app.route("/messier.html")
def messier_html_redirect():
    """
    Обратная совместимость: старые ссылки на /messier.html → /game/messier.
    """
    return redirect("/game/messier", code=301)


# ── Генерация карт ───────────────────────────────────────────────────────────


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    mode = data.get("mode", "stereo")

    dtime = (
        datetime.fromisoformat(data["datetime"])
        if data.get("datetime")
        else datetime.utcnow()
    )
    v_mag_limit = float(data.get("v_mag_limit", 6.5))
    constraints = CatalogConstraints(max_magnitude=v_mag_limit)

    flags = {
        "add_ecliptic": data.get("add_ecliptic", False),
        "add_equator": data.get("add_equator", False),
        "add_galactic_equator": data.get("add_galactic_equator", False),
        "add_planets": data.get("add_planets", False),
        "add_equatorial_grid": data.get("add_equatorial_grid", False),
        "add_constellations": data.get("add_constellations", False),
        "add_constellations_names": data.get("add_constellation_names", False),
    }

    # Whether to print observation info block on the task page (stereo only)
    print_skychart_info = bool(data.get("print_skychart_info", False))

    tmp_path = os.path.join(
        tempfile.gettempdir(), f"skychart_{uuid.uuid4().hex}.pdf"
    )

    if mode == "stereo":
        config = StereoProjConfig(
            local_time=dtime,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            **flags,
        )
        proj = StereoProjector(
            config=config,
            catalog=CATALOG,
            planets_catalog=PlanetCatalog(),
            constellation_config=ConstellationConfig(),
        )
        fig, ax = proj.generate(constraints=constraints)
        save_figure_skychart(
            fig=fig,
            filename=tmp_path,
            config=config,
            location_name="",
            logo_path=os.path.join(
                BASE_DIR, "src", "helpers", "pdf_helpers", "logo_astrageek.png"
            ),
            footer_text="skychart.astrageek.ru",
            print_skychart_info=print_skychart_info,
        )

    elif mode == "pinhole":
        constellation = data.get("constellation", "ORI").upper()
        center = get_constellation_center(constellation)
        camera_cfg = CameraConfig.from_fov_and_aspect(
            fov_deg=float(data.get("fov", 60)),
            aspect_ratio=float(data.get("aspect_ratio", 1.5)),
            height_pix=int(data.get("height_pix", 1000)),
        )
        shot_cond = ShotConditions(
            center_direction=center,
            tilt_angle=float(data.get("tilt_angle", 0)),
        )
        config = PinholeConfig(local_time=dtime, **flags)
        projector = Pinhole(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=config,
            constellation_config=ConstellationConfig(),
            catalog=CATALOG,
            planet_catalog=PlanetCatalog(),
        )
        fig, ax = projector.generate(constraints=constraints)
        save_figure_pinhole(
            fig=fig,
            filename=tmp_path,
            logo_path="src/helpers/pdf_helpers/logo_astrageek.png",
            footer_text="skychart.astrageek.ru",
        )

    return send_file(
        tmp_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="skychart.pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
