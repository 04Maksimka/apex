"""Usage example of pinhole projection."""
from matplotlib import pyplot as plt

from constellations_metadata.contellations_centers import get_constellation_dir, \
    Constellation
from hip_catalog.hip_catalog import Catalog
from pinhole_projection.pinhole_projector import ShotConditions, CameraCfg, \
    Pinhole
from planets_catalog.planet_catalog import PlanetCatalog, Planets


def example_visualization():
    """Create example visualization of pinhole projections."""
    from datetime import datetime

    # Create catalogs
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)

    planet_catalog = PlanetCatalog()

    camera_cfg = CameraCfg(
        width=1024,
        height=768,
        foc_len=1500.0
    )

    time = datetime(2024, 1, 1, 0, 0, 0)

    # Example: Pointing at specific region (Orion)
    print("\nExample: Pointing at Orion region")
    shot_cond = ShotConditions(
        center_dir=get_constellation_dir(Constellation.ORI),
        tilt_angle=180,
    )

    pinhole = Pinhole(shot_cond, camera_cfg, time, catalog, planet_catalog)
    result = pinhole.project(include_constellations=True)

    # Create visualizations
    fig, ax = plt.subplots(1, 1, figsize=(15, 18))

    sizes = (6.5 - result.stars['v_mag']) ** 1.3
    ax.scatter(result.stars['x_pix'], result.stars['y_pix'], s=sizes)

    plt.show()

if __name__ == '__main__':
    example_visualization()