import os
import uuid
import tempfile

import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, send_file, jsonify, redirect, url_for
from datetime import datetime

from src.web.messier_blueprint import messier_bp
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.stereographic_projection.stereographic_projector import (
    StereoProjector, StereoProjConfig, ConstellationConfig
)
from src.pinhole_projection.pinhole_projector import (
    PinholeConfig, CameraConfig, ShotConditions, Pinhole
)
from src.helpers.pdf_helpers.figure2pdf import save_figure_skychart, save_figure_pinhole
from src.constellations_metadata.constellations_data import get_constellation_center
from src.web.game_blueprint import game_bp

app = Flask(__name__, static_folder="public_html", static_url_path="")
app.register_blueprint(messier_bp)
app.register_blueprint(game_bp)

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# BASE_DIR = корень проекта AstraGeek/

CATALOG = Catalog(
    catalog_name=os.path.join(BASE_DIR, "src", "hip_catalog", "hip_data.tsv"),
    use_cache=True,
)


# ── Основные страницы ─────────────────────────────────────────────────────────

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
    """Обратная совместимость: старые ссылки на /messier.html → /game/messier."""
    return redirect("/game/messier", code=301)


# ── Генерация карт ────────────────────────────────────────────────────────────

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    mode = data.get("mode", "stereo")

    dtime = datetime.fromisoformat(data.get("datetime", datetime.now().isoformat()))

    if mode == "stereo":
        lat  = float(data.get("lat", 55.75))
        lon  = float(data.get("lon", 37.62))
        mag  = float(data.get("mag", 5.5))
        config = StereoProjConfig(
            local_time=dtime,
            latitude=lat,
            longitude=lon,
            limiting_magnitude=mag,
            add_planets=data.get("add_planets", True),
            add_ecliptic=data.get("add_ecliptic", True),
            add_equator=data.get("add_equator", True),
            add_galactic_equator=data.get("add_galactic_equator", False),
            add_constellations=data.get("add_constellations", True),
            add_constellations_names=data.get("add_constellations_names", True),
            add_grid=data.get("add_grid", True),
            use_dark_mode=data.get("use_dark_mode", True),
        )
        constraints = CatalogConstraints(limiting_magnitude=mag)
        stars  = CATALOG.get_stars(constraints)
        planets = PlanetCatalog()
        proj   = StereoProjector(config)
        fig    = proj.plot(stars, planets)

    else:  # pinhole
        ra_center  = float(data.get("ra",  0.0))
        dec_center = float(data.get("dec", 0.0))
        fov        = float(data.get("fov", 20.0))
        mag        = float(data.get("mag", 7.0))
        roll       = float(data.get("roll", 0.0))

        constellation = data.get("constellation")
        if constellation:
            ra_center, dec_center = get_constellation_center(constellation)

        conditions = ShotConditions(ra=ra_center, dec=dec_center, roll=roll)
        camera     = CameraConfig(
            fov_width=fov,
            fov_height=fov,
            image_width=int(data.get("width", 800)),
            image_height=int(data.get("height", 800)),
        )
        config = PinholeConfig(
            local_time=dtime,
            limiting_magnitude=mag,
            add_planets=data.get("add_planets", False),
            add_ecliptic=data.get("add_ecliptic", False),
            add_equator=data.get("add_equator", False),
            add_galactic_equator=data.get("add_galactic_equator", False),
            add_constellations=data.get("add_constellations", True),
            add_constellations_names=data.get("add_constellations_names", True),
            add_ticks=data.get("add_ticks", True),
            add_equatorial_grid=data.get("add_equatorial_grid", False),
            use_dark_mode=data.get("use_dark_mode", True),
            constellation_config=ConstellationConfig(names=[constellation]) if constellation else None,
        )
        constraints = CatalogConstraints(limiting_magnitude=mag)
        stars   = CATALOG.get_stars(constraints)
        planets = PlanetCatalog()
        pinhole = Pinhole(conditions, camera, config)
        fig     = pinhole.plot(stars, planets)

    output_format = data.get("format", "png").lower()
    tmp = tempfile.NamedTemporaryFile(
        suffix=f".{output_format}", delete=False, dir=tempfile.gettempdir()
    )
    tmp.close()

    if output_format == "pdf":
        if mode == "stereo":
            save_figure_skychart(fig, tmp.name)
        else:
            save_figure_pinhole(fig, tmp.name)
        mimetype = "application/pdf"
    else:
        fig.savefig(tmp.name, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        mimetype = "image/png"

    import matplotlib.pyplot as plt
    plt.close(fig)

    return send_file(
        tmp.name,
        mimetype=mimetype,
        as_attachment=True,
        download_name=f"skychart.{output_format}",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)