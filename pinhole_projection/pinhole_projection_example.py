"""Usage example of pinhole projection."""
import numpy as np
from matplotlib import pyplot as plt

from constellations_metadata.contellations_centers import get_constellation_dir, \
    Constellation
from hip_catalog.hip_catalog import Catalog
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
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)
    planet_catalog = PlanetCatalog()

    fov_deg = 60
    aspect_ratio = 1.5
    height = 1000

    camera_cfg = CameraCfg.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=aspect_ratio,
        height_pix=height
    )

    time = datetime(2024, 1, 1, 0, 0, 0)
    shot_cond = ShotConditions(
        center_dir=get_constellation_dir(constellation),
        tilt_angle=tilt_angle,
    )

    pinhole = Pinhole(shot_cond, camera_cfg, time, catalog, planet_catalog)
    result = pinhole.project()
    # Create visualizations
    color = 'black'
    if use_dark_mode:
        color = 'white'
        plt.style.use('dark_background')
    fig, ax = plt.subplots(1, 1, figsize=(15, 18))
    sizes = (6.0 - result.stars['v_mag']) ** 1.5
    ax.scatter(result.stars['x_pix'], result.stars['y_pix'], s=sizes, c=color)
    ax.invert_xaxis()

    if remove_ticks:
        ax.set_xticks([])
        ax.set_yticks([])


if __name__ == '__main__':
    example_pinhole_visualization(
        constellation=Constellation.UMA,
        tilt_angle=180,
        use_dark_mode=False,
        remove_ticks=True,
    )

    plt.show()