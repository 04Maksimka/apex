"""Implementation of cylindrical projection showing planets' movement across the sky.

This module creates visualizations (gif) of planetary motion using a cylindrical (equirectangular)
projection, which maps the celestial sphere onto a flat rectangle. This is useful for
tracking planetary positions over time and visualizing their paths through the zodiac.
On the visualisation there is a  scatter plot for each planet at each tic of time of given interval.
"""
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dataclasses import dataclass

from src.planets_catalog.planet_catalog import PlanetCatalog, Planets
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints


@dataclass
class CylindricProjectionConfig:
    """Configuration for cylindrical projection animation."""
    start_time: datetime
    end_time: datetime
    time_step: timedelta  # Time between frames
    output_filename: str = "planets_movement.gif"
    fps: int = 10
    dpi: int = 100
    figsize: Tuple[float, float] = (16, 8)

    # Visual settings
    show_stars: bool = True
    star_max_magnitude: float = 5.0
    show_ecliptic: bool = True
    show_grid: bool = True
    grid_spacing: float = 15.0  # degrees
    dark_mode: bool = True


class CylindricPlanetsMovement:
    """Creates cylindrical projection animations of planetary motion."""

    def __init__(self, config: CylindricProjectionConfig):
        """
        Initialize the cylindrical projection animator.

        Args:
            config: Configuration for the animation
        """
        self.config = config
        self.planet_catalog = PlanetCatalog()
        self.star_catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)

        # Generate time steps
        self.times = self._generate_time_steps()

        # Pre-compute star positions (they don't change over short periods)
        if self.config.show_stars:
            constraints = CatalogConstraints(
                max_magnitude=self.config.star_max_magnitude)
            self.stars = self.star_catalog.get_stars(constraints)
        else:
            self.stars = None

    def _generate_time_steps(self) -> List[datetime]:
        """Generate list of datetime objects for animation frames."""
        times = []
        current_time = self.config.start_time

        while current_time <= self.config.end_time:
            times.append(current_time)
            current_time += self.config.time_step

        return times

    def _ra_dec_to_cylindric(self, ra: np.ndarray, dec: np.ndarray) -> Tuple[
        np.ndarray, np.ndarray]:
        """Convert RA/Dec to cylindrical projection coordinates.

        :param ra: Right ascension in radians
        :param dec: Declination in radians
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray:
        :param dec: np.ndarray:
        :param ra: np.ndarray: 
        :param dec: np.ndarray: 
        :returns: Tuple of->
        :rtype: x

        """
        x = np.rad2deg(ra) % 360
        y = np.rad2deg(dec)
        return x, y

    def _create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create and configure the figure for animation."""
        if self.config.dark_mode:
            plt.style.use('dark_background')
            bg_color = 'black'
            grid_color = 'gray'
            text_color = 'white'
        else:
            plt.style.use('default')
            bg_color = 'white'
            grid_color = 'lightgray'
            text_color = 'black'

        fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Set limits and aspect
        ax.set_xlim(0, 360)
        ax.set_ylim(-90, 90)
        ax.set_aspect('equal')

        # Labels
        ax.set_xlabel('Right Ascension (degrees)', fontsize=12,
                      color=text_color)
        ax.set_ylabel('Declination (degrees)', fontsize=12, color=text_color)

        # Grid
        if self.config.show_grid:
            ax.grid(True, alpha=0.3, color=grid_color, linestyle='--',
                    linewidth=0.5)
            ax.set_xticks(np.arange(0, 361, self.config.grid_spacing))
            ax.set_yticks(np.arange(-90, 91, self.config.grid_spacing))

        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        return fig, ax

    def _plot_stars(self, ax: plt.Axes):
        """Plot background stars on the axes.

        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes: 

        """
        if self.stars is None:
            return

        ra = self.stars['ra']
        dec = self.stars['dec']
        v_mag = self.stars['v_mag']

        x, y = self._ra_dec_to_cylindric(ra, dec)

        # Star sizes based on magnitude
        sizes = (6.0 - v_mag) ** 1.8

        color = 'white' if self.config.dark_mode else 'black'
        ax.scatter(x, y, s=sizes, c=color, alpha=0.6, zorder=1)

    def _plot_ecliptic(self, ax: plt.Axes):
        """Plot the ecliptic line.

        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes:
        :param ax: plt.Axes: 

        """
        # The ecliptic is at roughly 23.5 degrees inclination to the celestial equator
        # For simplicity, we'll draw a sinusoidal curve
        ra_points = np.linspace(0, 360, 1000)

        # Approximate ecliptic: dec = 23.5 * sin(ra)
        # This is simplified - proper calculation would use obliquity and convert from ecliptic coords
        obliquity = 23.44  # degrees
        dec_points = obliquity * np.sin(np.deg2rad(ra_points))

        color = 'yellow' if self.config.dark_mode else 'orange'
        ax.plot(ra_points, dec_points, color=color, alpha=0.5,
                linewidth=1.5, linestyle='--', label='Ecliptic', zorder=2)

    def _get_planet_positions(self, time: datetime) -> dict:
        """Get positions of all planets at given time.

        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime: 

        """
        planets_data = self.planet_catalog.get_planets(time)

        positions = {}
        for i, planet_enum in enumerate(Planets):
            planet_data = planets_data[i]
            ra = planet_data['ra']
            dec = planet_data['dec']
            x, y = self._ra_dec_to_cylindric(np.array([ra]), np.array([dec]))

            positions[planet_enum] = {
                'x': x[0],
                'y': y[0],
                'v_mag': planet_data['v_mag']
            }

        return positions

    def create_animation(self):
        """Create the animation and save it as a GIF."""
        fig, ax = self._create_figure()

        # Plot static elements
        self._plot_stars(ax)
        if self.config.show_ecliptic:
            self._plot_ecliptic(ax)

        # Create scatter plots for each planet (will be updated in animation)
        planet_scatters = {}

        for planet in Planets:
            color = self.planet_catalog.get_planet_color(planet)
            scatter = ax.scatter([], [], s=150, c=color,
                                 label=planet.name.capitalize(),
                                 edgecolors='white' if self.config.dark_mode else 'black',
                                 linewidths=1, zorder=5, alpha=0.9)
            planet_scatters[planet] = scatter

        # Add legend
        ax.legend(loc='upper right', fontsize=8, framealpha=0.8)

        # Time text
        time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                            verticalalignment='top', fontsize=10,
                            bbox=dict(boxstyle='round', facecolor='wheat',
                                      alpha=0.5))

        def init():
            """Initialize animation."""
            for scatter in planet_scatters.values():
                scatter.set_offsets(np.empty((0, 2)))
            time_text.set_text('')
            return list(planet_scatters.values()) + [time_text]

        def update(frame_idx):
            """Update animation frame.

            :param frame_idx: 

            """
            time = self.times[frame_idx]
            positions = self._get_planet_positions(time)

            # Update planet positions
            for planet, scatter in planet_scatters.items():
                pos = positions[planet]
                x, y = pos['x'], pos['y']

                # Update scatter
                scatter.set_offsets([[x, y]])

            # Update time text
            time_text.set_text(f'Date: {time.strftime("%Y-%m-%d %H:%M")}')

            return list(planet_scatters.values()) + [time_text]

        # Create animation
        anim = FuncAnimation(fig, update, init_func=init,
                             frames=len(self.times),
                             interval=1000 / self.config.fps,
                             blit=True, repeat=True)

        # Save animation
        writer = PillowWriter(fps=self.config.fps)
        print(f"Saving animation to {self.config.output_filename}...")
        anim.save(self.config.output_filename, writer=writer,
                  dpi=self.config.dpi)
        print(f"Animation saved successfully!")

        return fig, anim

def example_planets():
    """Example: Track planets over a few months."""
    config = CylindricProjectionConfig(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2026, 12, 31),
        time_step=timedelta(days=2),
        output_filename="planets_2024-2026.gif",
        fps=20,
        star_max_magnitude=5.5,
        show_ecliptic=True,
        show_grid=True,
        dark_mode=True,
        figsize=(18, 9)
    )

    animator = CylindricPlanetsMovement(config)
    fig, anim = animator.create_animation()
    plt.show()


if __name__ == '__main__':
    # Run the example
    example_planets()