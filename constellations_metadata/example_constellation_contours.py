"""Enhanced example of pinhole projection with constellation contours.

This example demonstrates how to visualize star fields with constellation
line patterns overlaid on the projection.
"""
from matplotlib import pyplot as plt
from datetime import datetime
from typing import List, Optional

from constellations_metadata.contellations_centers import (
    get_constellation_dir, 
    Constellation
)
from hip_catalog.hip_catalog import Catalog
from pinhole_projection.constellation_renderer import ConstellationRenderer, \
    draw_constellation_lines, draw_multiple_constellations
from pinhole_projection.pinhole_projector import (
    ShotConditions, 
    CameraCfg,
    Pinhole
)
from planets_catalog.planet_catalog import PlanetCatalog


def visualize_constellation_with_contours(
    constellation: Constellation,
    tilt_angle: float = 0,
    fov_deg: float = 60,
    aspect_ratio: float = 1.5,
    height: int = 1000,
    time: Optional[datetime] = None,
    use_dark_mode: bool = True,
    remove_ticks: bool = True,
    show_constellation_lines: bool = True,
    line_color: str = 'cyan',
    line_width: float = 1.2,
    line_alpha: float = 0.8,
    show_planets: bool = False,
    title: Optional[str] = None,
):
    """
    Create visualization of a constellation with contour lines.
    
    Args:
        constellation: Target constellation
        tilt_angle: Camera tilt angle in degrees
        fov_deg: Horizontal field of view in degrees
        aspect_ratio: Width/height ratio
        height: Image height in pixels
        time: Observation time (default: 2024-01-01 00:00:00)
        use_dark_mode: Use dark background
        remove_ticks: Remove axis ticks
        show_constellation_lines: Draw constellation contour lines
        line_color: Color for constellation lines
        line_width: Width of constellation lines
        line_alpha: Transparency of constellation lines
        show_planets: Draw planets if visible
        title: Custom plot title
    """
    # Setup catalogs
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)
    planet_catalog = PlanetCatalog()
    
    # Setup camera
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=aspect_ratio,
        height_pix=height
    )
    
    # Setup time
    if time is None:
        time = datetime(2024, 1, 1, 0, 0, 0)
    
    # Setup shot conditions
    shot_cond = ShotConditions(
        center_direction=get_constellation_dir(constellation),
        tilt_angle=tilt_angle,
    )
    
    # Create pinhole projector
    pinhole = Pinhole(shot_cond, camera_cfg, time, catalog, planet_catalog)
    result = pinhole.project()
    
    # Setup plot style
    if use_dark_mode:
        plt.style.use('dark_background')
        star_color = 'white'
        bg_color = 'black'
    else:
        plt.style.use('default')
        star_color = 'black'
        bg_color = 'white'
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 12 / aspect_ratio))
    
    # Draw stars
    star_sizes = (6.0 - result.stars['v_mag']) ** 1.8
    ax.scatter(
        result.stars['x_pix'], 
        result.stars['y_pix'], 
        s=star_sizes, 
        c=star_color,
        alpha=0.9,
        zorder=2  # Stars above lines
    )
    
    # Draw constellation lines
    if show_constellation_lines:
        renderer = ConstellationRenderer(pinhole)
        segments = renderer.get_constellation_segments(constellation, result.stars)
        
        if segments:
            draw_constellation_lines(
                ax, 
                segments,
                color=line_color,
                linewidth=line_width,
                alpha=line_alpha
            )
            print(f"Drew {len(segments)} line segments for {constellation.value}")
        else:
            print(f"No visible line segments for {constellation.value}")
    
    # Draw planets if requested
    if show_planets and len(result.planets) > 0:
        planet_sizes = (6.0 - result.planets['v_mag']) ** 1.8 * 2
        ax.scatter(
            result.planets['x_pix'],
            result.planets['y_pix'],
            s=planet_sizes,
            c='yellow',
            marker='*',
            edgecolors='orange',
            linewidths=0.5,
            alpha=0.9,
            zorder=3,
            label='Planets'
        )
        if len(result.planets) > 0:
            ax.legend()
    
    # Set plot limits and appearance
    ax.set_xlim(0, camera_cfg.width)
    ax.set_ylim(0, camera_cfg.height)
    ax.invert_xaxis()
    ax.set_aspect('equal')
    
    if remove_ticks:
        ax.set_xticks([])
        ax.set_yticks([])
    
    # Set title
    if title is None:
        title = f"{constellation.value} Constellation"
        if show_constellation_lines:
            title += " with Contours"
    ax.set_title(title, fontsize=14, pad=15)
    
    # Add info text
    info_text = f"FOV: {fov_deg}° | Time: {time.strftime('%Y-%m-%d %H:%M')} | Stars: {len(result.stars)}"
    ax.text(
        0.02, 0.02, 
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.7)
    )
    
    plt.tight_layout()
    return fig, ax


def visualize_multiple_constellations(
    constellations: List[Constellation],
    center_constellation: Optional[Constellation] = None,
    tilt_angle: float = 0,
    fov_deg: float = 90,
    aspect_ratio: float = 1.5,
    height: int = 1200,
    time: Optional[datetime] = None,
    use_dark_mode: bool = True,
    remove_ticks: bool = True,
    constellation_colors: Optional[dict] = None,
    line_width: float = 1.0,
    line_alpha: float = 0.7,
):
    """
    Visualize multiple constellation contours in a single view.
    
    Args:
        constellations: List of constellations to display
        center_constellation: Constellation to center on (default: first in list)
        tilt_angle: Camera tilt angle
        fov_deg: Field of view
        aspect_ratio: Width/height ratio
        height: Image height in pixels
        time: Observation time
        use_dark_mode: Use dark background
        remove_ticks: Remove axis ticks
        constellation_colors: Optional dict mapping constellations to colors
        line_width: Width of constellation lines
        line_alpha: Transparency of constellation lines
    """
    # Setup
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)
    planet_catalog = PlanetCatalog()
    
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=aspect_ratio,
        height_pix=height
    )
    
    if time is None:
        time = datetime(2024, 1, 1, 0, 0, 0)
    
    # Center on specified constellation or first in list
    if center_constellation is None:
        center_constellation = constellations[0]
    
    shot_cond = ShotConditions(
        center_direction=get_constellation_dir(center_constellation),
        tilt_angle=tilt_angle,
    )
    
    # Create projection
    pinhole = Pinhole(shot_cond, camera_cfg, time, catalog, planet_catalog)
    result = pinhole.project()
    
    # Setup plot
    if use_dark_mode:
        plt.style.use('dark_background')
        star_color = 'white'
        bg_color = 'black'
    else:
        plt.style.use('default')
        star_color = 'black'
        bg_color = 'white'
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 14 / aspect_ratio))
    
    # Draw stars
    star_sizes = (6.0 - result.stars['v_mag']) ** 1.8
    ax.scatter(
        result.stars['x_pix'],
        result.stars['y_pix'],
        s=star_sizes,
        c=star_color,
        alpha=0.9,
        zorder=2
    )
    
    # Draw constellation lines
    renderer = ConstellationRenderer(pinhole)
    constellation_segments = renderer.get_multiple_constellation_segments(
        constellations, 
        result.stars
    )
    
    if constellation_segments:
        draw_multiple_constellations(
            ax,
            constellation_segments,
            color='cyan',
            linewidth=line_width,
            alpha=line_alpha,
            color_map=constellation_colors
        )
        
        total_segments = sum(len(segs) for segs in constellation_segments.values())
        print(f"Drew {total_segments} line segments across {len(constellation_segments)} constellations")
    
    # Set appearance
    ax.set_xlim(0, camera_cfg.width)
    ax.set_ylim(0, camera_cfg.height)
    ax.invert_xaxis()
    ax.set_aspect('equal')
    
    if remove_ticks:
        ax.set_xticks([])
        ax.set_yticks([])
    
    # Title
    const_names = ", ".join([c.value for c in constellations[:3]])
    if len(constellations) > 3:
        const_names += f" and {len(constellations) - 3} more"
    ax.set_title(f"Multiple Constellations: {const_names}", fontsize=14, pad=15)
    
    # Info
    info_text = f"FOV: {fov_deg}° | Time: {time.strftime('%Y-%m-%d %H:%M')} | Stars: {len(result.stars)}"
    ax.text(
        0.02, 0.02,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.7)
    )
    
    plt.tight_layout()
    return fig, ax


# Example usage
if __name__ == '__main__':
    # Example 1: Single constellation with contours
    print("Example 1: Ursa Major with constellation lines")
    fig1, ax1 = visualize_constellation_with_contours(
        constellation=Constellation.UMA,
        tilt_angle=180,
        fov_deg=50,
        use_dark_mode=True,
        line_color='cyan',
        line_width=1.5,
        line_alpha=0.9,
    )
    
    # Example 2: Orion with contours
    print("\nExample 2: Orion constellation")
    fig2, ax2 = visualize_constellation_with_contours(
        constellation=Constellation.ORI,
        tilt_angle=0,
        fov_deg=60,
        use_dark_mode=True,
        line_color='orange',
        line_width=1.2,
    )
    
    # Example 3: Multiple constellations
    print("\nExample 3: Multiple constellations in wide field")
    constellations_to_show = [
        Constellation.UMA,
        Constellation.UMI,
        Constellation.DRA,
        Constellation.CAS,
    ]
    
    color_map = {
        Constellation.UMA: 'cyan',
        Constellation.UMI: 'yellow',
        Constellation.DRA: 'magenta',
        Constellation.CAS: 'lime',
    }
    
    fig3, ax3 = visualize_multiple_constellations(
        constellations=constellations_to_show,
        center_constellation=Constellation.UMA,
        fov_deg=120,
        use_dark_mode=True,
        constellation_colors=color_map,
        line_width=1.3,
    )
    
    print("\nDisplaying all visualizations...")
    plt.show()
