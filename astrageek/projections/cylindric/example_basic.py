from matplotlib import pyplot as plt

from astrageek.catalogs.hip import Catalog, CatalogConstraints
from astrageek.catalogs.planets import PlanetCatalog
from astrageek.helpers.pdf_helpers.figure2pdf import save_figure
from astrageek.projections.cylindric import (
    CylindricConfig,
    CylindricProjector,
)


def example_basic_usage():
    """Basic example of cylindrical projection."""
    from datetime import datetime

    # Create configuration
    config = CylindricConfig(
        local_time=datetime(2024, 6, 21, 22, 0),
        add_grid=True,
        add_ecliptic=True,
        add_equator=True,
        add_planets=True,
        add_constellations_names=True,
        use_dark_mode=True,
        figsize=(18, 9),
    )

    # Create catalogs
    star_catalog = Catalog(catalog_name="hip_data.tsv", use_cache=False)
    planet_catalog = PlanetCatalog()

    # Create projector
    projector = CylindricProjector(
        config=config, catalog=star_catalog, planets_catalog=planet_catalog
    )

    # Generate visualization
    constraints = CatalogConstraints(max_magnitude=6.0)
    fig, ax = projector.generate(constraints=constraints)

    save_figure(fig, "cylindric_proj")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    example_basic_usage()
