"""Implementation of a pinhole projection with Mars retrograde movement.

This module creates static visualizations showing the retrograde motion of Mars
against the background of stars. The retrograde motion
is the apparent backward movement of planets as Earth overtakes them in orbit.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

from pinhole_projection.pinhole_projector import Pinhole, ShotConditions, \
    CameraCfg
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from planets_catalog.planet_catalog import PlanetCatalog, Planets
from constellations_metadata.contellations_centers import Constellation, \
    get_constellation_dir


@dataclass
class RetrogradeVisualizationConfig:
    """Configuration for static retrograde motion visualization."""
    start_time: datetime
    end_time: datetime
    time_step: timedelta

    # Camera configuration
    center_direction: np.ndarray  # Direction to point camera
    tilt_angle: float = 0.0
    fov_deg: float = 60.0
    aspect_ratio: float = 1.5
    height_pix: int = 1200

    # Visual settings
    star_max_magnitude: float = 6.0
    show_constellation_lines: bool = False
    show_date_labels: bool = True
    annotate_key_points: bool = True  # Mark stationary points
    dark_mode: bool = True
    output_filename: str = "mars_retrograde.png"
    dpi: int = 150


class StaticRetrogradeMovement:
    """Creates static visualizations of Mars retrograde motion."""

    def __init__(self, config: RetrogradeVisualizationConfig):
        """
        Initialize the retrograde motion visualizer.

        Args:
            config: Configuration for the visualization
        """
        self.config = config
        self.catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)
        self.planet_catalog = PlanetCatalog()

        # Create camera configuration
        self.camera_cfg = CameraCfg.from_fov_and_aspect(
            fov_deg=config.fov_deg,
            aspect_ratio=config.aspect_ratio,
            height_pix=config.height_pix
        )

        # Generate time steps
        self.times = self._generate_time_steps()

    def _generate_time_steps(self) -> List[datetime]:
        """Generate list of datetime objects for Mars positions."""
        times = []
        current_time = self.config.start_time

        while current_time <= self.config.end_time:
            times.append(current_time)
            current_time += self.config.time_step

        return times

    def _create_pinhole_at_time(self, time: datetime) -> Pinhole:
        """Create a Pinhole projector for a specific time."""
        shot_cond = ShotConditions(
            center_dir=self.config.center_direction,
            tilt_angle=self.config.tilt_angle
        )

        return Pinhole(
            shot_cond=shot_cond,
            camera_cfg=self.camera_cfg,
            time=time,
            catalog=self.catalog,
            planet_catalog=self.planet_catalog
        )

    def _get_mars_positions(self) -> List[Tuple[float, float, datetime]]:
        """Get Mars positions at all time steps."""
        mars_positions = []

        for time in self.times:
            pinhole = self._create_pinhole_at_time(time)
            planets = pinhole.get_planets()

            # Find Mars
            mars_mask = planets['planet_id'] == Planets.MARS.value

            if np.any(mars_mask):
                mars_data = planets[mars_mask][0]
                x_pix = float(mars_data['x_pix'])
                y_pix = float(mars_data['y_pix'])
                mars_positions.append((x_pix, y_pix, time))

        return mars_positions

    def _detect_stationary_points(self, positions: List[
        Tuple[float, float, datetime]]) -> List[int]:
        """
        Detect stationary points where Mars changes direction.

        Returns indices of approximate stationary points.
        """
        if len(positions) < 3:
            return []

        x_coords = np.array([pos[0] for pos in positions])
        y_coords = np.array([pos[1] for pos in positions])

        # Calculate velocity components
        vx = np.diff(x_coords)
        vy = np.diff(y_coords)

        # Calculate speed
        speed = np.sqrt(vx ** 2 + vy ** 2)

        # Find local minima in speed (stationary points)
        stationary_indices = []
        for i in range(1, len(speed) - 1):
            if speed[i] < speed[i - 1] and speed[i] < speed[i + 1]:
                # Check if it's a significant minimum
                if speed[i] < np.mean(speed) * 0.5:
                    stationary_indices.append(i)

        return stationary_indices

    def create_visualization(self):
        """Create a static visualization showing Mars retrograde motion."""
        # Setup figure
        if self.config.dark_mode:
            plt.style.use('dark_background')
            bg_color = 'black'
            text_color = 'white'
            mars_trail_color = 'red'
        else:
            plt.style.use('default')
            bg_color = 'white'
            text_color = 'black'
            mars_trail_color = 'darkred'

        figsize = (self.camera_cfg.width / 100, self.camera_cfg.height / 100)
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.dpi)

        # Set limits
        ax.set_xlim(0, self.camera_cfg.width)
        ax.set_ylim(0, self.camera_cfg.height)
        ax.set_aspect('equal')

        # Remove ticks
        ax.set_xticks([])
        ax.set_yticks([])

        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        # Invert x-axis
        ax.invert_xaxis()

        # Plot stars (using the first time step)
        print("Plotting background stars...")
        pinhole_ref = self._create_pinhole_at_time(self.times[0])
        constraints = CatalogConstraints(
            max_magnitude=self.config.star_max_magnitude)
        stars = pinhole_ref.get_stars(constraints)

        if len(stars) > 0:
            star_coords = np.column_stack([stars['x_pix'], stars['y_pix']])
            star_sizes = (6.5 - stars['v_mag']) ** 1.8
            ax.scatter(star_coords[:, 0], star_coords[:, 1],
                       s=star_sizes,
                       c='white' if self.config.dark_mode else 'black',
                       alpha=0.7, zorder=1)

        # Get Mars positions
        print("Computing Mars positions...")
        mars_positions = self._get_mars_positions()

        if len(mars_positions) == 0:
            print(
                "Warning: Mars not visible in field of view during this period!")
            return fig

        print(f"Found {len(mars_positions)} Mars positions")

        # Extract coordinates
        x_coords = [pos[0] for pos in mars_positions]
        y_coords = [pos[1] for pos in mars_positions]
        dates = [pos[2] for pos in mars_positions]

        # Plot Mars trail
        ax.plot(x_coords, y_coords, color=mars_trail_color, linewidth=2.5,
                alpha=0.8, zorder=3, label='Mars Path')

        # Plot Mars positions as dots
        ax.scatter(x_coords, y_coords, c=mars_trail_color, s=80,
                   edgecolors='white' if self.config.dark_mode else 'black',
                   linewidths=1, zorder=4, alpha=0.9)

        # Detect and mark stationary points
        if self.config.annotate_key_points:
            stationary_idx = self._detect_stationary_points(mars_positions)

            if stationary_idx:
                print(f"Found {len(stationary_idx)} stationary points")
                for idx in stationary_idx:
                    x, y, date = mars_positions[idx]

                    # Draw a circle around stationary point
                    circle = plt.Circle((x, y), radius=20, fill=False,
                                        edgecolor='yellow', linewidth=2,
                                        linestyle='--', zorder=5)
                    ax.add_patch(circle)

                    # Add label
                    ax.annotate('Stationary\n' + date.strftime('%Y-%m-%d'),
                                xy=(x, y), xytext=(x + 40, y + 40),
                                fontsize=8, color='yellow',
                                bbox=dict(boxstyle='round,pad=0.5',
                                          facecolor=bg_color,
                                          edgecolor='yellow', alpha=0.8),
                                arrowprops=dict(arrowstyle='->', color='yellow',
                                                lw=1.5),
                                zorder=6)

        # Add date labels at regular intervals
        if self.config.show_date_labels:
            label_interval = max(1, len(mars_positions) // 8)
            for i in range(0, len(mars_positions), label_interval):
                x, y, date = mars_positions[i]

                # Add small label
                ax.annotate(date.strftime('%m/%d'),
                            xy=(x, y), xytext=(5, 5),
                            textcoords='offset points',
                            fontsize=7, color=text_color,
                            bbox=dict(boxstyle='round,pad=0.3',
                                      facecolor=bg_color,
                                      edgecolor=mars_trail_color, alpha=0.7),
                            zorder=6)

        # Mark start and end points
        x_start, y_start, date_start = mars_positions[0]
        x_end, y_end, date_end = mars_positions[-1]

        ax.scatter([x_start], [y_start], c='lime', s=200, marker='o',
                   edgecolors='white', linewidths=2, zorder=7,
                   label='Start: ' + date_start.strftime('%Y-%m-%d'))

        ax.scatter([x_end], [y_end], c='cyan', s=200, marker='s',
                   edgecolors='white', linewidths=2, zorder=7,
                   label='End: ' + date_end.strftime('%Y-%m-%d'))

        # Add title
        ax.set_title('Mars Retrograde Motion\n' +
                     f'{date_start.strftime("%Y-%m-%d")} to {date_end.strftime("%Y-%m-%d")}',
                     fontsize=14, color=text_color, pad=20, fontweight='bold')

        # Add legend
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

        # Add directional arrows to show retrograde motion
        if len(mars_positions) > 10:
            # Sample a few positions to draw direction arrows
            arrow_indices = [len(mars_positions) // 4,
                             len(mars_positions) // 2,
                             3 * len(mars_positions) // 4]

            for idx in arrow_indices:
                if idx > 0 and idx < len(mars_positions) - 1:
                    x1, y1, _ = mars_positions[idx - 1]
                    x2, y2, _ = mars_positions[idx]

                    dx = x2 - x1
                    dy = y2 - y1

                    # Normalize and scale
                    length = np.sqrt(dx ** 2 + dy ** 2)
                    if length > 0:
                        dx = dx / length * 30
                        dy = dy / length * 30

                        ax.arrow(x1, y1, dx, dy, head_width=15, head_length=10,
                                 fc='orange', ec='orange', linewidth=2,
                                 alpha=0.7, zorder=5)

        plt.tight_layout()

        # Save figure
        print(f"Saving visualization to {self.config.output_filename}...")
        fig.savefig(self.config.output_filename, dpi=self.config.dpi,
                    bbox_inches='tight', facecolor=bg_color)
        print("Visualization saved successfully!")

        return fig


def example_mars_retrograde_2022():
    """Example: Mars retrograde motion in 2022-2023 in Taurus/Gemini."""
    # Point camera toward Taurus/Gemini region
    center_dir = get_constellation_dir(Constellation.TAU)

    config = RetrogradeVisualizationConfig(
        start_time=datetime(2022, 9, 1),
        end_time=datetime(2023, 1, 31),
        time_step=timedelta(days=4),
        center_direction=center_dir,
        tilt_angle=0,
        fov_deg=70,
        aspect_ratio=16 / 9,
        height_pix=1200,
        star_max_magnitude=6.0,
        show_date_labels=True,
        annotate_key_points=True,
        dark_mode=True,
        output_filename="mars_retrograde_2022_taurus.png",
        dpi=150
    )

    visualizer = StaticRetrogradeMovement(config)
    fig = visualizer.create_visualization()
    plt.show()


def example_mars_retrograde_2024():
    """Example: Mars retrograde motion in 2024-2025 in Leo."""
    center_dir = get_constellation_dir(Constellation.LEO)

    config = RetrogradeVisualizationConfig(
        start_time=datetime(2024, 10, 1),
        end_time=datetime(2025, 2, 28),
        time_step=timedelta(days=5),
        center_direction=center_dir,
        tilt_angle=0,
        fov_deg=75,
        aspect_ratio=1.5,
        height_pix=1400,
        star_max_magnitude=5.5,
        show_date_labels=True,
        annotate_key_points=True,
        dark_mode=True,
        output_filename="mars_retrograde_2024_leo.png",
        dpi=200
    )

    visualizer = StaticRetrogradeMovement(config)
    fig = visualizer.create_visualization()
    plt.show()


def example_mars_retrograde_wide_view():
    """Example: Wide view capturing full retrograde loop."""
    # Point toward ecliptic plane
    center_dir = np.array([1.0, 0.0, 0.1])
    center_dir = center_dir / np.linalg.norm(center_dir)

    config = RetrogradeVisualizationConfig(
        start_time=datetime(2022, 8, 15),
        end_time=datetime(2023, 2, 15),
        time_step=timedelta(days=3),
        center_direction=center_dir,
        tilt_angle=0,
        fov_deg=90,
        aspect_ratio=2.0,
        height_pix=1000,
        star_max_magnitude=5.5,
        show_date_labels=True,
        annotate_key_points=True,
        dark_mode=True,
        output_filename="mars_retrograde_wide.png",
        dpi=150
    )

    visualizer = StaticRetrogradeMovement(config)
    fig = visualizer.create_visualization()
    plt.show()


if __name__ == '__main__':
    # Run the example
    example_mars_retrograde_2022()
