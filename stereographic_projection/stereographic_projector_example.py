from hip_catalog.hip_catalog import CatalogConstraints, Catalog
from planets_catalog.planet_catalog import PlanetCatalog
from stereographic_projection.stereographic_projector import StereoProjector, StereoProjConfig
from helpers.pdf_helpers.figure2pdf import save_figure_skychart
from datetime import datetime


# Configure catalog
constraints = CatalogConstraints(
    max_magnitude=5.5,
)

# Configure projection: date, time and place
config = StereoProjConfig(
    add_ecliptic=True,
    add_equator=False,
    add_galactic_equator=False,
    add_planets=True,
    add_ticks=False,
    add_horizontal_grid=False,
    add_equatorial_grid=True,
    grid_theta_step=10.0,
    grid_phi_step=45.0,
    random_origin=True,
    local_time=datetime(
        year=2004,
        month=6,
        day=14,
        hour=6,
        minute=10,
        second=0,
    ),
    latitude=43.0,
    longitude=131.5,
)

# Create catalog object (without data)
catalog = Catalog(
    catalog_name='hip_data.tsv',
    cache_dir='cache',
    use_cache=True,
)

# Create projector object with configuration
proj = StereoProjector(
    config=config,
    catalog=catalog,
    planets_catalog=PlanetCatalog()
)

# Make figure with constrains
figure = proj.generate(constraints=constraints)

# Save skychart
save_figure_skychart(
    fig=figure,
    filename="polar_scatter_local_logo.pdf",
    config=config,
    location_name="",
    logo_path="helpers/pdf_helpers/logo_astrageek.png",
    footer_text="Generate more on skychart.astrageek.ru.",
    logo_position=(0.12, 0.97),
    text_position=(0.5, 0.01),
    print_skychart_info=False,
)