"""Enhanced example of pinhole projection with constellation contours.

This example demonstrates how to visualize star fields with constellation
line patterns overlaid on the projection.
"""

from datetime import datetime
from typing import List, Optional

import numpy as np
from matplotlib import pyplot as plt

from src.constellations_metadata.constellations_data import (
    get_constellation_center,
)
from src.helpers.constellations.constellation_renderer_pinhole import (
    ConstellationRenderer,
    draw_constellation_lines_collection,
    draw_multiple_constellations,
)
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.pinhole_projection.pinhole_projector import (
    CameraConfig,
    Pinhole,
    PinholeConfig,
    ShotConditions,
)
from src.planets_catalog.planet_catalog import PlanetCatalog


def visualize_constellation_with_contours(
    constellation: str,
    tilt_angle: float = 0,
    fov_deg: float = 60,
    aspect_ratio: float = 1.5,
    height: int = 1000,
    time: Optional[datetime] = None,
    use_dark_mode: bool = True,
    add_ticks: bool = False,
    add_planets: bool = False,
    add_ecliptic: bool = False,
    add_equator: bool = False,
    add_galactic_equator: bool = False,
    add_equatorial_grid: bool = False,
    show_constellation_lines: bool = True,
    line_color: str = "cyan",
    line_width: float = 1.2,
    line_alpha: float = 0.8,
    title: Optional[str] = None,
):
    """Create visualization of a constellation with contour lines."""

    # Setup catalogs
    catalog = Catalog(catalog_name="hip_data.tsv", use_cache=False)
    planet_catalog = PlanetCatalog()

    # Setup camera
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg, aspect_ratio=aspect_ratio, height_pix=height
    )

    # Setup time
    if time is None:
        time = datetime(2024, 1, 1, 0, 0, 0)

    # Setup shot conditions
    shot_cond = ShotConditions(
        center_direction=np.asarray(get_constellation_center(constellation)),
        tilt_angle=tilt_angle,
    )

    constraints = CatalogConstraints(max_magnitude=6.0)

    config = PinholeConfig(
        add_ticks=add_ticks,
        use_dark_mode=use_dark_mode,
        add_planets=add_planets,
        add_ecliptic=add_ecliptic,
        add_equator=add_equator,
        add_galactic_equator=add_galactic_equator,
        add_equatorial_grid=add_equatorial_grid,
        local_time=time,
    )

    # Create pinhole projector and figure
    pinhole = Pinhole(shot_cond, camera_cfg, config, catalog, planet_catalog)
    fig, ax = pinhole.generate(constraints=constraints)
    result = pinhole.projection_result

    # Draw constellation lines
    if show_constellation_lines:
        renderer = ConstellationRenderer()
        segments = renderer.get_constellation_segments(
            constellation, result.stars
        )
        print(segments)

        if segments:
            draw_constellation_lines_collection(
                ax,
                segments,
                color=line_color,
                linewidth=line_width,
                alpha=line_alpha,
            )
            print(f"Drew {len(segments)} line segments for {constellation}")
        else:
            print(f"No visible line segments for {constellation}")

    # Set title
    if title is None:
        title = f"{constellation} Constellation"
        if show_constellation_lines:
            title += " with Contours"
    ax.set_title(title, fontsize=14, pad=15)

    # Add info text
    info_text = (
        f"FOV: {fov_deg}° | Time: "
        f"{time.strftime('%Y-%m-%d %H:%M')} | Stars:"
        f" {len(result.stars)}"
    )
    ax.text(
        0.02,
        0.02,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7),
    )

    plt.tight_layout()
    return fig, ax


def visualize_multiple_constellations(
    constellations: List[str],
    center_constellation: Optional[str] = None,
    tilt_angle: float = 0,
    fov_deg: float = 90,
    aspect_ratio: float = 1.5,
    height: int = 1200,
    time: Optional[datetime] = None,
    use_dark_mode: bool = True,
    add_ticks: bool = False,
    add_planets: bool = False,
    add_ecliptic: bool = False,
    add_equator: bool = False,
    add_galactic_equator: bool = False,
    add_equatorial_grid: bool = False,
    constellation_colors: Optional[dict] = None,
    line_width: float = 1.0,
    line_alpha: float = 0.7,
):
    """Visualize multiple constellation contours in a single view."""

    # Setup
    catalog = Catalog(catalog_name="hip_data.tsv", use_cache=False)
    planet_catalog = PlanetCatalog()

    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg, aspect_ratio=aspect_ratio, height_pix=height
    )

    if time is None:
        time = datetime(2024, 1, 1, 0, 0, 0)

    # Center on specified constellation or first in list
    if center_constellation is None:
        center_constellation = constellations[0]

    shot_cond = ShotConditions(
        center_direction=np.asarray(
            get_constellation_center(center_constellation)
        ),
        tilt_angle=tilt_angle,
    )

    config = PinholeConfig(
        add_ticks=add_ticks,
        use_dark_mode=use_dark_mode,
        add_planets=add_planets,
        add_ecliptic=add_ecliptic,
        add_equator=add_equator,
        add_galactic_equator=add_galactic_equator,
        add_equatorial_grid=add_equatorial_grid,
        local_time=time,
    )

    constraints = CatalogConstraints(max_magnitude=6.0)

    # Create projection
    pinhole = Pinhole(shot_cond, camera_cfg, config, catalog, planet_catalog)
    fig, ax = pinhole.generate(constraints=constraints)
    result = pinhole.projection_result

    # Draw constellation lines
    renderer = ConstellationRenderer()
    constellation_segments = renderer.get_multiple_constellation_segments(
        constellations, result.stars
    )

    if constellation_segments:
        draw_multiple_constellations(
            ax,
            constellation_segments,
            color="cyan",
            linewidth=line_width,
            alpha=line_alpha,
            color_map=constellation_colors,
        )

        total_segments = sum(
            len(segs) for segs in constellation_segments.values()
        )
        print(
            f"Drew {total_segments} line segments across"
            f"{len(constellation_segments)} constellations"
        )

    # Title
    const_names = ", ".join([c for c in constellations[:3]])
    if len(constellations) > 3:
        const_names += f" and {len(constellations) - 3} more"
    ax.set_title(
        f"Multiple Constellations: {const_names}", fontsize=14, pad=15
    )

    # Info
    info_text = (
        f"FOV: {fov_deg}° |"
        f"Time: {time.strftime('%Y-%m-%d %H:%M')} |"
        f"Stars: {len(result.stars)}"
    )
    ax.text(
        0.02,
        0.02,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7),
    )

    plt.tight_layout()
    return fig, ax


# Example usage
if __name__ == "__main__":
    # Example 1: Single constellation with contours
    print("Example 1: Ursa Major with constellation lines")
    fig1, ax1 = visualize_constellation_with_contours(
        constellation="UMA",
        tilt_angle=180,
        fov_deg=50,
        line_color="cyan",
        line_width=1.5,
        line_alpha=0.9,
        use_dark_mode=False,
        add_ticks=False,
        add_planets=True,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_equatorial_grid=True,
    )

    # Example 2: Orion with contours
    print("\nExample 2: Hercules constellation")
    fig2, ax2 = visualize_constellation_with_contours(
        constellation="HER",
        fov_deg=60,
        line_color="orange",
        line_width=1.2,
        tilt_angle=0.0,
        use_dark_mode=False,
        add_ticks=False,
        add_planets=True,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_equatorial_grid=True,
    )

    # Example 3: Multiple constellations
    print("\nExample 3: Multiple constellations in wide field")
    constellations_to_show = [
        "HER",
        "OPH",
        "LYR",
    ]

    color_map = {
        "HER": "cyan",
        "OPH": "yellow",
        "LYR": "magenta",
    }

    fig3, ax3 = visualize_multiple_constellations(
        constellations=constellations_to_show,
        center_constellation="LYR",
        fov_deg=120,
        constellation_colors=color_map,
        line_width=1.3,
        tilt_angle=0.0,
        use_dark_mode=False,
        add_ticks=False,
        add_planets=True,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_equatorial_grid=True,
    )

    print("\nDisplaying all visualizations...")
    plt.show()
