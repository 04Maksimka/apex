"""Usage example of pinhole projection."""
import numpy as np
from matplotlib import pyplot as plt

from constellations_metadata.contellations_centers import get_constellation_dir, \
    Constellation
from helpers.geometry.geometry import mag_to_radius
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from pinhole_projection.pinhole_projector import ShotConditions, CameraCfg, \
    Pinhole
from planets_catalog.planet_catalog import PlanetCatalog
from datetime import datetime


def example_pinhole_visualization(
        constellation: Constellation,
        tilt_angle: float = 0,
        use_dark_mode: bool = True,
        remove_ticks: bool = True,
):
    """Create example visualization of pinhole projections."""
    # Create catalogs
    constraints = CatalogConstraints(max_magnitude=6.0)
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=True)
    planet_catalog = PlanetCatalog()

    # Define camera configuration
    fov_deg = 90
    aspect_ratio = 1.5
    height = 1000
    camera_cfg = CameraCfg.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=aspect_ratio,
        height_pix=height
    )

    # Set time
    time = datetime(2024, 1, 1, 0, 0, 0)
    # And shot conditions
    shot_cond = ShotConditions(
        center_dir=get_constellation_dir(constellation),
        tilt_angle=tilt_angle,
    )
    # Define pinhole camera with all the configurations
    pinhole = Pinhole(shot_cond, camera_cfg, time, catalog, planet_catalog)
    # Make a shot
    result = pinhole.project(constraints=constraints)

    # Create visualizations
    color = 'black'
    if use_dark_mode:
        color = 'white'
        plt.style.use('dark_background')
    fig, ax = plt.subplots(1, 1, figsize=(15, 18))

    sizes = mag_to_radius(
        magnitude=result.stars['v_mag'],
        constraints=constraints
    )

    ax.scatter(result.stars['x_pix'], result.stars['y_pix'], s=sizes, c=color)

    if remove_ticks:
        ax.set_xticks([])
        ax.set_yticks([])


if __name__ == '__main__':
    example_pinhole_visualization(
        constellation=Constellation.UMI,
        tilt_angle=0.0,
        use_dark_mode=False,
        remove_ticks=False,
    )

    plt.show()