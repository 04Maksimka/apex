from datetime import datetime
from typing import Tuple

import click
import numpy as np
from projections.pinhole import (
    CameraConfig,
    Pinhole,
    PinholeConfig,
    ShotConditions,
)

from astrageek.catalogs.constellations import (
    get_constellation_center,
)
from astrageek.catalogs.hip import Catalog, CatalogConstraints
from astrageek.catalogs.planets import PlanetCatalog
from astrageek.helpers.cli.cli import DependentOption
from astrageek.helpers.geometry.geometry import generate_random_direction
from astrageek.helpers.pdf_helpers.figure2pdf import (
    save_figure_pinhole,
    save_figure_skychart,
)
from astrageek.messier_game.game import messier_game
from astrageek.projections.stereographic import (
    ConstellationConfig,
    StereoProjConfig,
    StereoProjector,
)


# Helper function
def resolve(preset, explicit, name):
    """
    Helper function to get preset value
    of given flag (name) or return an explicit value.

    :param preset: preset value
    :param name: param name
    :param explicit: explicit value
    """

    if explicit is not None:
        return explicit
    return preset.get(name, False)  # from preset or False


@click.group()
@click.version_option(version="0.1.0", prog_name="AstraGeek")
def cli():
    """AstraGeek — star sky map generator."""
    pass


@cli.command()
@click.option(
    "--latitude",
    "-lat",
    default=0.0,
    type=float,
    help="Observer's latitude in degrees (default 0.0).",
)
@click.option(
    "--longitude",
    "-lon",
    default=0.0,
    type=float,
    help="Observer's longitude in degrees (default 0.0).",
)
@click.option(
    "--dtime",
    "-t",
    type=click.DateTime(
        formats=[
            "%Y-%m-%d %H:%M:%S",  # 2025-01-15 22:30:00
            "%Y-%m-%d %H:%M",  # 2025-01-15 22:30
            "%Y-%m-%dT%H:%M:%S",  # 2025-01-15T22:30:00 (ISO 8601)
            "%Y-%m-%dT%H:%M",  # 2025-01-15T22:30
            "%Y-%m-%d",  # 2025-01-15 (time = 00:00)
            "%d.%m.%Y %H:%M",  # 15.01.2025 22:30
            "%d.%m.%Y",  # 15.01.2025
        ]
    ),
    default=None,
    required=False,
    help="Date and time. Formats examples:"
    "'2025-01-15 22:30', '2025-01-15', '15.01.2025 22:30'.",
)
@click.option(
    "--mode",
    type=click.Choice(["teacher", "student"]),
    default=None,
    help="Mode presets for teacher and student. The student setting contains "
    "all flags in the off state, resulting in a blank map with no symbols"
    " or notes The teacher setting contains all symbols and answers",
)
@click.option(
    "--add-ticks/--no-ticks",
    is_flag=True,
    default=None,
    help="Adds ticks: cardinal directions and azimuth marks.",
)
@click.option(
    "--random-origin/--no-random-origin",
    is_flag=True,
    default=None,
    help="Randomizes map orientation.",
)
@click.option(
    "--add-ecliptic/--no-ecliptic",
    is_flag=True,
    default=None,
    help="Adds the great circle of the ecliptic to the map",
)
@click.option(
    "--add-equator/--no-equator",
    is_flag=True,
    default=None,
    help="Adds the great circle of the celestial equator to the map.",
)
@click.option(
    "--add_galactic_equator/--no_galactic_equator",
    is_flag=True,
    default=None,
    help="Adds the great circle of the galactic equator to the map.",
)
@click.option(
    "--add-planets/--no-planets",
    is_flag=True,
    default=None,
    help="Marks planet's positions.",
)
@click.option(
    "--add-horizontal-grid/--no-horizontal-grid",
    is_flag=True,
    default=None,
    help="Adds an azimuthal coordinate grid to the map with "
    "a specified step on each axis (see the --grid-steps option below)",
)
@click.option(
    "--add-equatorial-grid/--no-equatorial-grid",
    is_flag=True,
    default=None,
    help="Adds an equatorial coordinate grid to the map with "
    "a specified step on each axis (see the --grid-steps option)",
)
@click.option(
    "--grid-steps",
    type=click.Tuple([float, float]),
    default=(15.0, 15.0),
    cls=DependentOption,
    depends_on=["add_equatorial_grid", "add_horizontal_grid"],
    help="Grid steps in degrees (requires grids).",
)
@click.option(
    "--add-zenith/--no-zenith",
    is_flag=True,
    default=None,
    help="Adds the zenith label to the map. ",
)
@click.option(
    "--add-poles/--no-poles",
    is_flag=True,
    default=None,
    help="Adds the visible celestial pole label to the map.",
)
@click.option(
    "--add-constellations/--no-constellations",
    is_flag=True,
    default=None,
    help="Adds constellations lines to the map.",
)
@click.option(
    "--add-constellations-names/--no-constellations-names",
    is_flag=True,
    default=None,
    help="Add constellation labels (three-letter latin abbreviations.",
)
@click.option(
    "--mag-limit",
    default=5.5,
    type=float,
    help="Sets map magnitude top limit (default 5.5).",
)
@click.option(
    "--output",
    default="polar_scatter_local_logo.pdf",
    type=click.Path(),
    help="Sets output filename.",
)
def stereographic(
    latitude: float,
    longitude: float,
    dtime: datetime,
    mode: str,
    add_ticks: bool,
    random_origin: bool,
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
    add_constellations_names: bool,
    mag_limit: float,
    output: str,
):
    """Plot stereographic projection of the skymap."""

    # Check time
    if dtime is None:
        dtime = datetime.now()

    # Present for teacher and student mode
    PRESETS = {
        "teacher": dict(
            add_ecliptic=True,
            add_equator=True,
            add_galactic_equator=True,
            add_planets=True,
            add_ticks=True,
            add_horizontal_grid=False,
            add_equatorial_grid=True,
            random_origin=True,
            add_constellations=True,  # Constellations lines
            add_constellations_names=True,  # Constellations names
            add_zenith=True,
            add_poles=True,
        ),
        "student": dict(
            add_ecliptic=False,
            add_equator=False,
            add_galactic_equator=False,
            add_planets=False,
            add_ticks=False,
            add_horizontal_grid=False,
            add_equatorial_grid=False,
            random_origin=True,
            add_zenith=False,
            add_poles=False,
        ),
    }
    preset = PRESETS.get(mode, {})

    # Read flags
    flags = {
        "add_ticks": resolve(preset, add_ticks, "add_ticks"),
        "random_origin": resolve(preset, random_origin, "random_origin"),
        "add_ecliptic": resolve(preset, add_ecliptic, "add_ecliptic"),
        "add_equator": resolve(preset, add_equator, "add_equator"),
        "add_galactic_equator": resolve(
            preset, add_galactic_equator, "add_galactic_equator"
        ),
        "add_planets": resolve(preset, add_planets, "add_planets"),
        "add_horizontal_grid": resolve(
            preset, add_horizontal_grid, "add_horizontal_grid"
        ),
        "add_equatorial_grid": resolve(
            preset, add_equatorial_grid, "add_equatorial_grid"
        ),
        "add_zenith": resolve(preset, add_zenith, "add_zenith"),
        "add_poles": resolve(preset, add_poles, "add_poles"),
        "add_constellations": resolve(
            preset, add_constellations, "add_constellations"
        ),
        "add_constellations_names": resolve(
            preset, add_constellations_names, "add_constellations_names"
        ),
    }

    # Print info
    click.echo(f"Mode: {mode or 'custom'}")
    for k, v in flags.items():
        status = "+" if v else "-"
        click.echo(f"  {status} {k}")

    # === Specify projector ===
    # Set catalog constraints
    constraints = CatalogConstraints(
        max_magnitude=mag_limit,
    )

    # Configure projection: date, time and place and other flags
    config = StereoProjConfig(
        grid_theta_step=grid_steps[0],
        grid_phi_step=grid_steps[1],
        local_time=dtime,
        latitude=latitude,
        longitude=longitude,
        **flags,
    )

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellation_linewidth=0.5,
        constellation_alpha=0.5,
    )

    # Create catalog object (without data)
    catalog = Catalog(
        catalog_name="astrageek/hip/hip_data.tsv",
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
        logo_path="astrageek/helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generate more on skychart.astrageek.ru.",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
        print_skychart_info=False,
    )


@cli.command()
@click.option(
    "--dtime",
    "-t",
    type=click.DateTime(
        formats=[
            "%Y-%m-%d %H:%M:%S",  # 2025-01-15 22:30:00
            "%Y-%m-%d %H:%M",  # 2025-01-15 22:30
            "%Y-%m-%dT%H:%M:%S",  # 2025-01-15T22:30:00 (ISO 8601)
            "%Y-%m-%dT%H:%M",  # 2025-01-15T22:30
            "%Y-%m-%d",  # 2025-01-15 (time = 00:00)
            "%d.%m.%Y %H:%M",  # 15.01.2025 22:30
            "%d.%m.%Y",  # 15.01.2025
        ]
    ),
    default=None,
    required=False,
    help="Date and time. Formats examples:"
    "'2025-01-15 22:30', '2025-01-15', '15.01.2025 22:30'.",
)
@click.option(
    "--constellation",
    "-c",
    type=str,
    default=None,
    help="Constellation 3-letter code (e.g. ORI, UMA, CAS)."
    "Sets center direction.",
)
@click.option(
    "--random-direction",
    is_flag=True,
    default=False,
    help="Sets random sky direction as center."
    "Mutually exclusive with --constellation.",
)
@click.option(
    "--tilt-angle",
    type=float,
    default=0.0,
    help="Camera tilt angle in degrees.",
)
@click.option(
    "--fov", type=float, default=90.0, help="Field of view in degrees."
)
@click.option(
    "--aspect-ratio",
    type=float,
    default=1.5,
    help="Aspect ratio of the frame (default 1.5).",
)
@click.option(
    "--height-pix", type=int, default=1000, help="Image height in pixels."
)
@click.option(
    "--mode",
    type=click.Choice(["teacher", "student"]),
    default=None,
    help="Mode presets for teacher and student. The student setting contains "
    "all flags in the off state, resulting in a blank map with no symbols"
    " or notes.The teacher setting contains all symbols and answers",
)
@click.option(
    "--add-ecliptic/--no-ecliptic",
    is_flag=True,
    default=None,
    help="Adds the great circle of the ecliptic to the map",
)
@click.option(
    "--add-equator/--no-equator",
    is_flag=True,
    default=None,
    help="Adds the great circle of the celestial equator to the map.",
)
@click.option(
    "--add-galactic-equator/--no-galactic-equator",
    is_flag=True,
    default=None,
    help="Adds the great circle of the galactic equator to the map.",
)
@click.option(
    "--add-planets/--no-planets",
    is_flag=True,
    default=None,
    help="Marks planet's positions.",
)
@click.option(
    "--add-equatorial-grid/--no-equatorial-grid",
    is_flag=True,
    default=None,
    help="Adds an equatorial coordinate grid to the map with "
    "a specified step on each axis (see the --grid-steps option)",
)
@click.option(
    "--grid-steps",
    type=click.Tuple([float, float]),
    default=(15.0, 15.0),
    cls=DependentOption,
    depends_on=["add_equatorial_grid"],
    help="Grid steps in degrees (requires grids).",
)
@click.option(
    "--add-constellations/--no-constellations",
    is_flag=True,
    default=None,
    help="Adds constellations lines to the map.",
)
@click.option(
    "--add-constellations-names/--no-constellations-names",
    is_flag=True,
    default=None,
    help="Add constellation labels (three-letter latin abbreviations.",
)
@click.option(
    "--mag-limit",
    default=5.5,
    type=float,
    help="Sets map magnitude top limit (default 5.5).",
)
@click.option(
    "--output",
    default="polar_scatter_local_logo.pdf",
    type=click.Path(),
    help="Sets output filename.",
)
def pinhole(
    dtime: datetime,
    constellation: str,
    random_direction: bool,
    tilt_angle: float,
    fov: float,
    aspect_ratio: float,
    height_pix: int,
    mode: str,
    add_ecliptic: bool,
    add_equator: bool,
    add_galactic_equator: bool,
    add_planets: bool,
    add_equatorial_grid: bool,
    grid_steps: Tuple[float, float],
    add_constellations: bool,
    add_constellations_names: bool,
    mag_limit: float,
    output: str,
):
    """Plot pinhole projection of the skymap."""

    # Validation: constellation vs random-direction
    if constellation and random_direction:
        raise click.UsageError(
            "You cannot specify "
            "--constellation and --random-direction at the same time. "
            "Choose one or the other."
        )

    if not constellation and not random_direction:
        raise click.UsageError(
            "Specify the camera direction: "
            "--constellation ORI, for example or --random-direction."
        )

    # Set center_direction
    if constellation:
        constellation = constellation.upper()
        try:
            center = np.asarray(
                get_constellation_center(constellation), dtype=np.float32
            )
        except (KeyError, ValueError):
            raise click.BadParameter(
                f"Unknown constellation: '{constellation}'. "
                f"Use 3-letter IAU code (e.g. ORI, UMA, CAS).",
                param_hint="--constellation",
            )
        click.echo(f"Direction: constellation {constellation}")
    else:
        center = generate_random_direction()
        click.echo(f"Direction: random {center}")

    # Check time
    if dtime is None:
        dtime = datetime.now()

    # Presets for student and teacher mode
    PRESETS = {
        "teacher": dict(
            add_ecliptic=True,
            add_equator=True,
            add_galactic_equator=True,
            add_planets=True,
            add_equatorial_grid=True,
            add_constellations=True,  # Constellations lines
            add_constellations_names=True,  # Constellations names
        ),
        "student": dict(
            add_ecliptic=False,
            add_equator=False,
            add_galactic_equator=False,
            add_planets=False,
            add_equatorial_grid=False,
        ),
    }
    preset = PRESETS.get(mode, {})

    flags = {
        "add_ecliptic": resolve(preset, add_ecliptic, "add_ecliptic"),
        "add_equator": resolve(preset, add_equator, "add_equator"),
        "add_galactic_equator": resolve(
            preset, add_galactic_equator, "add_galactic_equator"
        ),
        "add_planets": resolve(preset, add_planets, "add_planets"),
        "add_equatorial_grid": resolve(
            preset, add_equatorial_grid, "add_equatorial_grid"
        ),
        "add_constellations": resolve(
            preset, add_constellations, "add_constellations"
        ),
        "add_constellations_names": resolve(
            preset, add_constellations_names, "add_constellations_names"
        ),
    }

    click.echo(f"Mode: {mode or 'custom'}")
    for k, v in flags.items():
        status = "+" if v else "-"
        click.echo(f"  {status} {k}")

    # === Specify projector ===
    # Specify catalog constraints
    constraints = CatalogConstraints(max_magnitude=mag_limit)

    # Make catalogs
    catalog = Catalog(catalog_name="hip_data.tsv", use_cache=True)
    planet_catalog = PlanetCatalog()

    # Configure projector
    config = PinholeConfig(
        local_time=dtime,
        grid_theta_step=grid_steps[0],
        grid_phi_step=grid_steps[1],
        **flags,
    )

    # Configure frame
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov,
        aspect_ratio=aspect_ratio,
        height_pix=height_pix,
    )

    # Configure direction and orientation
    shot_cond = ShotConditions(
        center_direction=center,
        tilt_angle=tilt_angle,
    )

    # Constellation viewing configurations
    constellation_config = ConstellationConfig(
        constellation_linewidth=0.5, constellation_alpha=0.5
    )

    # Define pinhole camera with all the configurations
    projector = Pinhole(
        shot_cond=shot_cond,
        camera_cfg=camera_cfg,
        config=config,
        constellation_config=constellation_config,
        catalog=catalog,
        planet_catalog=planet_catalog,
    )
    # Make a shot
    fig, ax = projector.generate(constraints=constraints)
    ax.set_aspect("equal")

    # Save skychart
    save_figure_pinhole(
        fig=fig,
        filename=output,
        logo_path="helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generate more on skychart.astrageek.ru.",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
    )


@cli.command()
def messier():
    """Messier Object Guessing Game.

    A game where players view a pinhole projection of a Messier object
    and try to guess its Messier number.
    """

    click.echo("=== Messier game ===")
    messier_game()
