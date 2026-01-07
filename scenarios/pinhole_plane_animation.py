"""Implementation of pinhole projection animation showing sky rotation and planetary motion.

This module creates animations of the night sky using pinhole camera projection,
showing the motion of planets in the Earth's sky over time. Neglect Earth rotation
around it's axis.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dataclasses import dataclass

from pinhole_projection.pinhole_projector import Pinhole, ShotConditions, CameraCfg
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from planets_catalog.planet_catalog import PlanetCatalog, Planets
from constellations_metadata.contellations_centers import Constellation, get_constellation_dir


@dataclass
class PinholeAnimationConfig:
    """Configuration for pinhole projection animation."""
    start_time: datetime
    end_time: datetime
    time_step: timedelta  # Time between frames

    # Camera configuration
    center_direction: np.ndarray  # Direction to point camera (unit vector in ECI)
    tilt_angle: float = 0.0  # Camera rotation angle in degrees
    fov_deg: float = 60.0  # Horizontal field of view
    aspect_ratio: float = 1.5  # Width/height ratio
    height_pix: int = 1000

    # Output settings
    output_filename: str = "pinhole_animation.gif"
    fps: int = 15
    dpi: int = 100

    # Visual settings
    star_max_magnitude: float = 5.5
    show_planet_labels: bool = True
    show_planet_trails: bool = True
    dark_mode: bool = True


class PinholePlaneAnimation:
    """Creates pinhole projection animations of the night sky."""

    def __init__(self, config: PinholeAnimationConfig):
        """
        Initialize the pinhole animation creator.

        Args:
            config: Configuration for the animation
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

        # Storage for planet trails
        self.planet_trails = {planet: {'x': [], 'y': []} for planet in Planets}

    def _generate_time_steps(self) -> List[datetime]:
        """Generate list of datetime objects for animation frames."""
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

    def _create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create and configure the figure for animation."""
        if self.config.dark_mode:
            plt.style.use('dark_background')
            bg_color = 'black'
            text_color = 'white'
        else:
            plt.style.use('default')
            bg_color = 'white'
            text_color = 'black'

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

        # Invert x-axis for proper star chart orientation
        ax.invert_xaxis()

        return fig, ax

    def create_animation(self):
        """Create the animation and save it as a GIF."""
        fig, ax = self._create_figure()

        # Initialize plot elements
        star_scatter = ax.scatter([], [], c='white' if self.config.dark_mode else 'black',
                                 s=[], alpha=0.8, zorder=1)

        planet_scatters = {}
        planet_trail_lines = {}
        planet_labels = {}

        for planet in Planets:
            color = self.planet_catalog.get_planet_color(planet)

            # Planet scatter
            scatter = ax.scatter([], [], s=200, c=color,
                               edgecolors='white' if self.config.dark_mode else 'black',
                               linewidths=1.5, zorder=5, alpha=0.95)
            planet_scatters[planet] = scatter

            # Trail line
            line, = ax.plot([], [], color=color, alpha=0.4, linewidth=2, zorder=3)
            planet_trail_lines[planet] = line

            # Label
            if self.config.show_planet_labels:
                label = ax.text(0, 0, '', fontsize=9, color=color,
                              bbox=dict(boxstyle='round,pad=0.3',
                                      facecolor=('black' if self.config.dark_mode else 'white'),
                                      alpha=0.6, edgecolor=color),
                              zorder=6, ha='left')
                planet_labels[planet] = label

        # Time text
        time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                           verticalalignment='top', fontsize=11,
                           color='white' if self.config.dark_mode else 'black',
                           bbox=dict(boxstyle='round',
                                   facecolor='black' if self.config.dark_mode else 'white',
                                   alpha=0.7))

        def init():
            """Initialize animation."""
            star_scatter.set_offsets(np.empty((0, 2)))
            star_scatter.set_sizes([])

            for scatter in planet_scatters.values():
                scatter.set_offsets(np.empty((0, 2)))

            for line in planet_trail_lines.values():
                line.set_data([], [])

            if self.config.show_planet_labels:
                for label in planet_labels.values():
                    label.set_position((0, 0))
                    label.set_text('')

            time_text.set_text('')

            artists = [star_scatter] + list(planet_scatters.values()) + list(planet_trail_lines.values())
            if self.config.show_planet_labels:
                artists += list(planet_labels.values())
            artists.append(time_text)

            return artists

        def update(frame_idx):
            """Update animation frame."""
            time = self.times[frame_idx]

            # Create pinhole projector for this time
            pinhole = self._create_pinhole_at_time(time)

            # Get star catalog constraints
            constraints = CatalogConstraints(max_magnitude=self.config.star_max_magnitude)

            # Get projected stars
            stars = pinhole.get_stars(constraints)

            if len(stars) > 0:
                star_coords = np.column_stack([stars['x_pix'], stars['y_pix']])
                star_sizes = (6.0 - stars['v_mag']) ** 1.5
                star_scatter.set_offsets(star_coords)
                star_scatter.set_sizes(star_sizes)
            else:
                star_scatter.set_offsets(np.empty((0, 2)))
                star_scatter.set_sizes([])

            # Get projected planets
            planets = pinhole.get_planets()

            for planet in Planets:
                # Find this planet in the results
                planet_mask = planets['planet_id'] == planet.value

                if np.any(planet_mask):
                    planet_data = planets[planet_mask][0]
                    x_pix = planet_data['x_pix']
                    y_pix = planet_data['y_pix']

                    # Update scatter
                    planet_scatters[planet].set_offsets([[x_pix, y_pix]])

                    # Update trail
                    if self.config.show_planet_trails:
                        self.planet_trails[planet]['x'].append(x_pix)
                        self.planet_trails[planet]['y'].append(y_pix)

                        # Keep only recent trail points
                        max_trail_length = max(1, len(self.times) // 4)
                        if len(self.planet_trails[planet]['x']) > max_trail_length:
                            self.planet_trails[planet]['x'].pop(0)
                            self.planet_trails[planet]['y'].pop(0)

                        trail_x = self.planet_trails[planet]['x']
                        trail_y = self.planet_trails[planet]['y']
                        planet_trail_lines[planet].set_data(trail_x, trail_y)

                    # Update label
                    if self.config.show_planet_labels:
                        planet_labels[planet].set_position((x_pix + 15, y_pix + 15))
                        planet_labels[planet].set_text(planet.name.capitalize())
                else:
                    # Planet not in FOV
                    planet_scatters[planet].set_offsets(np.empty((0, 2)))
                    planet_trail_lines[planet].set_data([], [])
                    if self.config.show_planet_labels:
                        planet_labels[planet].set_text('')

            # Update time text
            time_text.set_text(f'Date: {time.strftime("%Y-%m-%d %H:%M")}')

            artists = [star_scatter] + list(planet_scatters.values()) + list(planet_trail_lines.values())
            if self.config.show_planet_labels:
                artists += list(planet_labels.values())
            artists.append(time_text)

            return artists

        # Create animation
        print(f"Creating animation with {len(self.times)} frames...")
        anim = FuncAnimation(fig, update, init_func=init,
                           frames=len(self.times), interval=1000/self.config.fps,
                           blit=True, repeat=True)

        # Save animation
        writer = PillowWriter(fps=self.config.fps)
        print(f"Saving animation to {self.config.output_filename}...")
        anim.save(self.config.output_filename, writer=writer, dpi=self.config.dpi)
        print(f"Animation saved successfully!")

        return fig, anim


def example_mars_retrograde():
    """Example: Visualize Mars retrograde motion in Gemini constellation."""
    # Point camera at Gemini where Mars will show retrograde motion
    center_dir = get_constellation_dir(Constellation.GEM)

    config = PinholeAnimationConfig(
        start_time=datetime(2022, 10, 1),
        end_time=datetime(2023, 2, 1),
        time_step=timedelta(days=5),
        center_direction=center_dir,
        tilt_angle=0,
        fov_deg=80,
        output_filename="mars_retrograde_gemini.gif",
        fps=10,
        star_max_magnitude=5.5,
        show_planet_labels=True,
        show_planet_trails=True,
        dark_mode=True
    )

    animator = PinholePlaneAnimation(config)
    fig, anim = animator.create_animation()
    plt.show()


def example_planetary_conjunction():
    """Example: Visualize planetary conjunction."""
    # Point camera toward ecliptic region where conjunction will occur
    config = PinholeAnimationConfig(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 2, 28),
        time_step=timedelta(days=2),
        center_direction=np.array([1, 0, 0]),  # Point east
        tilt_angle=0,
        fov_deg=60,
        output_filename="planetary_conjunction.gif",
        fps=15,
        star_max_magnitude=5.0,
        show_planet_labels=True,
        show_planet_trails=True,
        dark_mode=True
    )

    animator = PinholePlaneAnimation(config)
    fig, anim = animator.create_animation()
    plt.show()


def example_ursa_major_with_planets():
    """Example: Ursa Major constellation with passing planets."""
    center_dir = get_constellation_dir(Constellation.UMA)

    config = PinholeAnimationConfig(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 12, 31),
        time_step=timedelta(days=1),
        center_direction=center_dir,
        tilt_angle=180,
        fov_deg=70,
        aspect_ratio=16/9,
        height_pix=1080,
        output_filename="ursa_major_yearly.gif",
        fps=20,
        star_max_magnitude=6.0,
        show_planet_labels=True,
        show_planet_trails=True,
        dark_mode=True
    )

    animator = PinholePlaneAnimation(config)
    fig, anim = animator.create_animation()
    plt.show()


if __name__ == '__main__':
    # Run the example
    example_mars_retrograde()
