"""Example of using stereographic projection with constellation rendering.

This example demonstrates how to create a stereographic sky chart with
constellation patterns overlaid on top of the stars.
"""
from datetime import datetime
import matplotlib.pyplot as plt

from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from planets_catalog.planet_catalog import PlanetCatalog
from stereographic_projector import (
    StereoProjector,
    StereoProjConfig, ConstellationConfig
)


def example_all_constellations():
    """Example 1: Show all available constellations."""
    print("Generating stereographic projection with all constellations...")

    # Projector configuration
    config = StereoProjConfig(
        local_time=datetime(2024, 6, 21, 23, 0),
        latitude=55.75,  # Moscow
        longitude=37.62,
        add_ecliptic=True,
        add_equator=True,
        add_ticks=True,
        add_constellations=True,  # Enable constellations

    )

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellation_color='cyan',
        constellation_linewidth=1.0,
        constellation_alpha=0.6,
    )

    # Star catalog constraints
    constraints = CatalogConstraints(
        max_magnitude=6.0,
        min_magnitude=-2.0,
    )

    # Create catalogs
    catalog = Catalog(
        catalog_name='hip_data.tsv',
        use_cache=True,
    )
    planets_catalog = PlanetCatalog()

    # Create projector with constellations
    projector = StereoProjector(
        config=config,
        catalog=catalog,
        constellation_config=constellation_config,
        planets_catalog=planets_catalog
    )

    # Generate projection
    fig, ax = projector.generate(constraints=constraints)

    return fig, ax


def example_specific_constellations():
    """Example 2: Show only specific constellations."""
    print("Generating stereographic projection with specific constellations...")

    # Select specific constellations
    selected_constellations = [
        'UMA',  # Ursa Major (Big Dipper)
        'UMI',  # Ursa Minor (Little Dipper)
        'CAS',  # Cassiopeia
        'ORI',  # Orion
        'LEO',  # Leo
    ]

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellations_list=selected_constellations,  # Only specific ones
        constellation_color='yellow',
        constellation_linewidth=1.2,
        constellation_alpha=0.8,
    )

    # Configuration
    config = StereoProjConfig(
        local_time=datetime(2024, 12, 21, 23, 0),  # Winter solstice night
        latitude=55.75,  # Moscow
        longitude=37.62,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_ticks=True,
        add_constellations=True,
    )

    # Star catalog constraints
    constraints = CatalogConstraints(
        max_magnitude=6.0,
        min_magnitude=-2.0,
    )

    # Create catalogs
    catalog = Catalog(
        catalog_name='hip_data.tsv',
        use_cache=True,
    )
    planets_catalog = PlanetCatalog()

    # Create projector
    projector = StereoProjector(
        config=config,
        constellation_config=constellation_config,
        catalog=catalog,
        planets_catalog=planets_catalog
    )

    # Generate projection
    fig, ax = projector.generate(constraints=constraints)

    return fig, ax


def example_colored_constellations():
    """Example 3: Show constellations with different colors."""
    print("Generating stereographic projection with colored constellations...")

    # Select constellations with custom colors
    color_map = {
        'UMA': 'brown',  # Big Dipper in yellow
        'ORI': 'gray',  # Orion in red
        'CYG': 'blue',  # Cygnus in cyan
        'LEO': 'red',  # Leo in orange
        'CAS': 'green',  # Cassiopeia in light green
    }

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellations_list=list(color_map.keys()),
        constellation_linewidth=1.5,
        constellation_alpha=0.75,
        constellation_color_map=color_map,
    )

    # Projector configuration
    config = StereoProjConfig(
        local_time=datetime(2024, 9, 22, 23, 0),  # Autumn equinox
        latitude=55.75,
        longitude=37.62,
        add_ticks=True,
        add_constellations=True,
        add_constellations_names=True
    )

    # Star catalog constraints
    constraints = CatalogConstraints(
        max_magnitude=6.0,
    )

    # Create catalogs
    catalog = Catalog(
        catalog_name='hip_data.tsv',
        use_cache=True,
    )
    planets_catalog = PlanetCatalog()

    # Create projector
    projector = StereoProjector(
        config=config,
        constellation_config=constellation_config,
        catalog=catalog,
        planets_catalog=planets_catalog
    )

    # Generate projection
    fig, ax = projector.generate(constraints=constraints)

    return fig, ax


def example_with_planets_and_grids():
    """Example 4: Complete sky chart with everything."""
    print(
        "Generating complete sky chart with constellations, planets, and grids...")

    # Configuration with all features
    config = StereoProjConfig(
        local_time=datetime(2024, 3, 20, 21, 0),  # Spring equinox evening
        latitude=55.75,
        longitude=37.62,
        grid_theta_step=15.0,
        grid_phi_step=15.0,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_planets=True,
        add_ticks=True,
        add_horizontal_grid=False,
        add_equatorial_grid=True,
        add_constellations=True,
        add_constellations_names=True
    )

    constellation_config = ConstellationConfig(
        constellation_color='lightgray',
        constellation_linewidth=0.8,
        constellation_alpha=1.0,
    )

    # Star catalog constraints
    constraints = CatalogConstraints(
        max_magnitude=5.5,
        min_magnitude=-2.0,
    )

    # Create catalogs
    catalog = Catalog(
        catalog_name='hip_data.tsv',
        use_cache=True,
    )
    planets_catalog = PlanetCatalog()

    # Create projector
    projector = StereoProjector(
        config=config,
        constellation_config=constellation_config,
        catalog=catalog,
        planets_catalog=planets_catalog
    )

    # Generate projection
    fig, ax = projector.generate(constraints=constraints)

    return fig, ax


if __name__ == '__main__':
    # Example 1: All constellations
    example_all_constellations()
    # Example 2: Specific constellations
    example_specific_constellations()
    # Example 3: Colored constellations
    example_colored_constellations()
    # Example 4: Complete chart
    example_with_planets_and_grids()

    plt.show()
