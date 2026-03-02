import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone

import matplotlib
import matplotlib.pyplot as plt
from flask import Flask, redirect, request, send_file

from src.constellations_metadata.constellations_data import (
    get_constellation_center,
)
from src.helpers.geometry.geometry import generate_random_direction
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

CATALOG = Catalog(
    catalog_name=os.path.join(BASE_DIR, "src", "hip_catalog", "hip_data.tsv"),
    use_cache=True,
)


def _warmup_catalogs():
    try:
        print("[warmup] Preloading game catalogues...")
        from src.game.question_factory import (
            _get_catalog,
            _get_messier_catalog,
            _load_named_stars,
        )

        _get_catalog()
        _get_messier_catalog()
        _load_named_stars()
        fig, _ax = plt.subplots()
        plt.close(fig)
        print("[warmup] Catalogs loaded")
    except Exception as exc:
        print(f"[warmup] Warning: {exc}")


threading.Thread(target=_warmup_catalogs, daemon=True).start()


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/generator")
def generator():
    return app.send_static_file("generator.html")


@app.route("/games")
def games_redirect():
    return redirect("/game/", code=301)


@app.route("/messier.html")
def messier_html_redirect():
    return redirect("/game/messier", code=301)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    mode = data.get("mode", "stereo")

    dtime = (
        datetime.fromisoformat(data["datetime"])
        if data.get("datetime")
        else datetime.now(timezone.utc)
    )
    v_mag_limit = float(data.get("v_mag_limit", 6.5))
    constraints = CatalogConstraints(max_magnitude=v_mag_limit)

    # grid_steps — общий для обоих режимов
    grid_theta = float(data.get("grid_theta_step", 15.0))
    grid_phi = float(data.get("grid_phi_step", 15.0))

    tmp_path = os.path.join(
        tempfile.gettempdir(), f"skychart_{uuid.uuid4().hex}.pdf"
    )

    if mode == "stereo":
        print_skychart_info = bool(data.get("print_skychart_info", False))
        flags = {
            "add_ecliptic": bool(data.get("add_ecliptic", False)),
            "add_equator": bool(data.get("add_equator", False)),
            "add_galactic_equator": bool(
                data.get("add_galactic_equator", False)
            ),
            "add_planets": bool(data.get("add_planets", False)),
            "add_horizontal_grid": bool(
                data.get("add_horizontal_grid", False)
            ),
            "add_equatorial_grid": bool(
                data.get("add_equatorial_grid", False)
            ),
            "add_constellations": bool(data.get("add_constellations", False)),
            "add_constellations_names": bool(
                data.get("add_constellations_names", False)
            ),
            "add_ticks": bool(data.get("add_ticks", False)),
            "add_zenith": bool(data.get("add_zenith", False)),
            "add_poles": bool(data.get("add_poles", False)),
            "random_origin": bool(data.get("random_origin", False)),
        }

        config = StereoProjConfig(
            local_time=dtime,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            grid_theta_step=grid_theta,
            grid_phi_step=grid_phi,
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
                BASE_DIR,
                "src",
                "helpers",
                "pdf_helpers",
                "logo_astrageek.png",
            ),
            footer_text="skychart.astrageek.ru",
            print_skychart_info=print_skychart_info,
        )
        plt.close(fig)

    elif mode == "pinhole":
        flags = {
            "add_ecliptic": bool(data.get("add_ecliptic", False)),
            "add_equator": bool(data.get("add_equator", False)),
            "add_galactic_equator": bool(
                data.get("add_galactic_equator", False)
            ),
            "add_planets": bool(data.get("add_planets", False)),
            "add_equatorial_grid": bool(
                data.get("add_equatorial_grid", False)
            ),
            "add_constellations": bool(data.get("add_constellations", False)),
            "add_constellations_names": bool(
                data.get("add_constellations_names", False)
            ),
        }

        random_direction = bool(data.get("random_direction", False))
        if random_direction:
            center = generate_random_direction()
        else:
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
        config = PinholeConfig(
            local_time=dtime,
            grid_theta_step=grid_theta,
            grid_phi_step=grid_phi,
            **flags,
        )
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
            logo_path=os.path.join(
                BASE_DIR,
                "src",
                "helpers",
                "pdf_helpers",
                "logo_astrageek.png",
            ),
            footer_text="skychart.astrageek.ru",
        )
        plt.close(fig)

    return send_file(
        tmp_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="skychart.pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
