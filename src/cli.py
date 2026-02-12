from typing import Tuple

import click
from datetime import datetime
from src.helpers.pdf_helpers.figure2pdf import save_figure_skychart
from src.hip_catalog.hip_catalog import CatalogConstraints, Catalog
from src.planets_catalog.planet_catalog import PlanetCatalog
from src.stereographic_projection.stereographic_projector import StereoProjector, \
    StereoProjConfig, ConstellationConfig  # импорт твоих функций
from src.pinhole_projection import pinhole_projector


@click.group()
@click.version_option(version="0.1.0", prog_name="AstraGeek")
def cli():
    """AstraGeek — генератор карт звёздного неба."""
    pass


@cli.command()
@click.option("--latitude", "-lat", required=True, type=float, help="Observer latitude in degrees.")
@click.option("--longitude", "-lon", required=True, type=float, help="Observer longitude in degrees.")
@click.option("--dtime", "-t",
    type=click.DateTime(formats=[
        "%Y-%m-%d %H:%M:%S",   # 2025-01-15 22:30:00
        "%Y-%m-%d %H:%M",      # 2025-01-15 22:30
        "%Y-%m-%dT%H:%M:%S",   # 2025-01-15T22:30:00 (ISO 8601)
        "%Y-%m-%dT%H:%M",      # 2025-01-15T22:30
        "%Y-%m-%d",            # 2025-01-15 (time = 00:00)
        "%d.%m.%Y %H:%M",      # 15.01.2025 22:30
        "%d.%m.%Y",            # 15.01.2025
    ]),
    default=None,
    required=False,
    help="Date and time. Formats examples: '2025-01-15 22:30', '2025-01-15', '15.01.2025 22:30'."
)
@click.option("--add-ecliptic", "-ec", is_flag=True, default=False, help="Add ecliptic on map.")
@click.option("--add-equator", "-eq", is_flag=True, default=False, help="Add celestial equator on map.")
@click.option("--add-galactic-equator", "-geq" , is_flag=True, default=False, help="Add galactic equator on map.")
@click.option("--add-planets", "-pl", is_flag=True, default=False, help="Add planets on map.")
@click.option("--add-horizontal-grid", "-hg",  is_flag=True, default=False, help="Add equatorial grid on map.")
@click.option("--add-equatorial-grid", "-eg",  is_flag=True, default=False, help="Add equatorial grid on map.")
@click.option(
    "--grid-steps",
    "-gs",
    type=click.Tuple([float, float]),
    default=(15.0, 15.0),
    help="Grid steps. First polar, second azimuthal grid step",
)
@click.option("--add-zenith", "-z", is_flag=True, default=False, help="Add zenith on map.")
@click.option("--add-poles", "-p", is_flag=True, default=False, help="Add celestial poles on map.")
@click.option("--add-constellations", "-c", is_flag=True, default=False, help="Add constellation lines on map.")
@click.option("--add-constellation-names", "-cn", is_flag=True, default=False, help="Add constellation labels on map.")
@click.option("--mag-limit", "-m", default=5.5, type=float, help="Map magnitude top limit (default 5.5).")
@click.option("--output", "-o", default="polar_scatter_local_logo.pdf", type=click.Path(), help="Output path.")
def stereographic(
        latitude: float,
        longitude: float,
        dtime: datetime,
        add_ecliptic: bool,
        add_equator: bool,
        add_galactic_equator: bool,
        add_planets: bool,
        add_horizontal_grid: bool,
        add_equatorial_grid: bool,
        grid_steps: Tuple[float, float],
        add_zenith: bool,
        add_poles: bool,
        add_constellations: bool,
        add_constellation_names: bool,
        mag_limit: float,
        output: str
):
    """Построить карту неба в стереографической проекции."""

    if dtime is None:
        dtime = datetime.now()

    click.echo(f"Map: lat={latitude}, lon={longitude}, dt={datetime}")

    constraints = CatalogConstraints(
        max_magnitude=mag_limit,
    )

    # Configure projection: date, time and place
    config = StereoProjConfig(
        add_ecliptic=add_ecliptic,
        add_equator=add_equator,
        add_galactic_equator=add_galactic_equator,
        add_planets=add_planets,
        add_ticks=False,
        add_horizontal_grid=add_horizontal_grid,
        add_equatorial_grid=add_equatorial_grid,
        add_zenith=add_zenith,
        add_poles=add_poles,
        add_constellations=add_constellations,
        add_constellations_names=add_constellation_names,
        grid_theta_step=grid_steps[0],
        grid_phi_step=grid_steps[1],
        random_origin=False,
        local_time=dtime,
        latitude=latitude,
        longitude=longitude,
    )

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellation_linewidth=0.5,
        constellation_alpha=0.5,
    )

    # Create catalog object (without data)
    catalog = Catalog(
        catalog_name='src/hip_catalog/hip_data.tsv',
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
        filename=output,
        config=config,
        location_name="",
        logo_path="src/helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generate more on skychart.astrageek.ru.",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
        print_skychart_info=False,
    )
