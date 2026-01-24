from ..hip_catalog.hip_catalog import CatalogConstraints, Catalog
from ..planets_catalog.planet_catalog import PlanetCatalog
from .stereographic_projector import StereoProjector, StereoProjConfig, ConstellationConfig
from ..helpers.pdf_helpers.figure2pdf import save_figure_skychart
from datetime import datetime


# Configure catalog
constraints = CatalogConstraints(
    max_magnitude=6.0,
)

# Configure projection: date, time and place
config = StereoProjConfig(
    add_ecliptic=True,
    add_equator=True,
    add_galactic_equator=True,
    add_planets=True,
    add_ticks=True,
    add_horizontal_grid=False,
    add_equatorial_grid=True,
    add_zenith=True,
    add_poles=True,
    add_constellations=True,
    grid_theta_step=15.0,
    grid_phi_step=15.0,
    random_origin=True,
    local_time=datetime(
        year=2004,
        month=6,
        day=14,
        hour=15,
        minute=10,
        second=0,
    ),
    latitude=45,
    longitude=180,
)

# Constellation viewing configurations
constellation_config = ConstellationConfig(
    constellation_linewidth=0.5,
    constellation_alpha=0.5,
)

# Create catalog object (without data)
catalog = Catalog(
    catalog_name='hip_data.tsv',
    use_cache=True,
)

# Create projector object with configuration
proj = StereoProjector(
    config=config,
    catalog=catalog,
    planets_catalog=PlanetCatalog(),
    constellation_config=constellation_config,
)

# Make figure with constrains
fig, ax = proj.generate(constraints=constraints)

# Save skychart
save_figure_skychart(
    fig=fig,
    filename="polar_scatter_local_logo.pdf",
    config=config,
    location_name="",
    logo_path="helpers/pdf_helpers/logo_astrageek.png",
    footer_text="Generate more on skychart.astrageek.ru.",
    logo_position=(0.12, 0.97),
    text_position=(0.5, 0.01),
    print_skychart_info=False,
)