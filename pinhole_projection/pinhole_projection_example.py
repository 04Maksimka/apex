"""Usage example of pinhole projection."""
import numpy as np
from matplotlib import pyplot as plt

from constellations_metadata.contellations_centers import get_constellation_dir, \
    Constellation
from helpers.pdf_helpers.figure2pdf import save_figure, save_figure_pinhole
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from pinhole_projection.pinhole_projector import ShotConditions, CameraConfig, \
    Pinhole, PinholeConfig
from planets_catalog.planet_catalog import PlanetCatalog
from datetime import datetime


def example_pinhole_visualization(
        constellation: Constellation,
        tilt_angle: float = 0,
        use_dark_mode: bool = True,
        add_ticks: bool = False,
        add_planets: bool = False,
        add_ecliptic: bool = False,
        add_equator: bool = False,
        add_galactic_equator: bool = False,
        add_horizontal_grid: bool = False,
        add_equatorial_grid: bool = False,
):
    """Create example visualization of pinhole projections."""
    # Create catalogs
    constraints = CatalogConstraints(max_magnitude=6.0)
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=True)
    planet_catalog = PlanetCatalog()

    # Set time
    time = datetime(2024, 1, 1, 0, 0, 0)
    # Define camera configuration
    fov_deg = 90
    aspect_ratio = 1.5
    height = 1000

    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=aspect_ratio,
        height_pix=height
    )

    config = PinholeConfig(
        add_ticks=add_ticks,
        use_dark_mode=use_dark_mode,
        add_planets=add_planets,
        add_ecliptic=add_ecliptic,
        add_equator=add_equator,
        add_galactic_equator=add_galactic_equator,
        add_horizontal_grid=add_horizontal_grid,
        add_equatorial_grid=add_equatorial_grid,
        local_time=time
    )

    # And shot conditions
    shot_cond = ShotConditions(
        center_direction=get_constellation_dir(constellation),
        tilt_angle=tilt_angle,
    )

    # Define pinhole camera with all the configurations
    pinhole = Pinhole(shot_cond, camera_cfg, config, catalog, planet_catalog)
    # Make a shot
    figure = pinhole.generate()

    # Save skychart
    save_figure_pinhole(
        fig=figure,
        filename="pinhole_local_logo.pdf",
        logo_path="helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generate more on skychart.astrageek.ru.",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
    )


if __name__ == '__main__':
    example_pinhole_visualization(
        constellation=Constellation.SGR,
        tilt_angle=0.0,
        use_dark_mode=False,
        add_ticks=False,
        add_planets=True,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_horizontal_grid=True,
        add_equatorial_grid=True,
    )


    plt.show()