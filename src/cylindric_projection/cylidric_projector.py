"""Module implementing cylindrical (equirectangular) projection.

The cylindrical projection maps the celestial sphere onto a rectangular plane,
where right ascension maps to x-coordinate and declination maps to y-coordinate.
This is particularly useful for visualizing the entire sky at once and tracking
object movements across the celestial sphere.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import numpy as np
from numpy.typing import NDArray
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

from ..constellations_metadata.constellations_data import (
    get_available_constellations,
    get_constellation_center
)
from ..helpers.geometry.geometry import mag_to_radius
from ..hip_catalog.hip_catalog import Catalog, CatalogConstraints
from ..planets_catalog.planet_catalog import PlanetCatalog, Planets


@dataclass
class CylindricConfig:
    """Configuration for cylindrical projection."""

    local_time: datetime
    latitude: float = 0.0
    longitude: float = 0.0

    # Display range in degrees
    ra_min: float = 0.0      # Right Ascension minimum (degrees)
    ra_max: float = 360.0    # Right Ascension maximum (degrees)
    dec_min: float = -90.0   # Declination minimum (degrees)
    dec_max: float = 90.0    # Declination maximum (degrees)

    # Grid settings
    grid_ra_step: float = 30.0   # RA grid step in degrees
    grid_dec_step: float = 15.0  # Dec grid step in degrees

    # Feature flags
    add_ecliptic: bool = False
    add_equator: bool = False
    add_galactic_equator: bool = False
    add_planets: bool = False
    add_grid: bool = True
    add_constellations: bool = False
    add_constellations_names: bool = False
    add_horizon: bool = False
    use_dark_mode: bool = False

    # Visual settings
    figsize: Tuple[float, float] = (16, 8)
    dpi: int = 100


@dataclass
class ConstellationConfig:
    """Configuration for constellation rendering."""

    constellations_list: Optional[List[str]] = None  # If None, render all available
    constellation_color: str = 'gray'
    constellation_linewidth: float = 0.8
    constellation_alpha: float = 0.7
    constellation_color_map: Optional[Dict[str, str]] = None


class CylindricProjector:
    """Class for cylindrical (equirectangular) projection of the celestial sphere."""

    def __init__(
            self,
            config: CylindricConfig,
            catalog: Catalog,
            planets_catalog: PlanetCatalog,
            constellation_config: Optional[ConstellationConfig] = None,
    ):
        """
        Initialize cylindrical projector.

        Args:
            config: Projection configuration
            catalog: Star catalog instance
            planets_catalog: Planet catalog instance
            constellation_config: Constellation rendering configuration
        """
        self.config = config
        self.constellation_config = constellation_config or ConstellationConfig()
        self.catalog = catalog
        self.planets_catalog = planets_catalog
        self._groups = {}  # Legend groups
        self._star_projections = None
        self._planets_projections = None
        self._fig = None
        self._ax = None

    def generate(self, constraints: Optional[CatalogConstraints] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Generate a cylindrical projection visualization.

        Args:
            constraints: Catalog constraints for star selection

        Returns:
            Tuple of (figure, axes)
        """
        # Create figure
        self._create_figure()

        # Project objects
        self.project(constraints=constraints)

        # Add optional features
        if self.config.add_grid:
            self._add_grid()

        if self.config.add_ecliptic:
            self._add_ecliptic()

        if self.config.add_equator:
            self._add_equator()

        if self.config.add_galactic_equator:
            self._add_galactic_equator()

        if self.config.add_horizon:
            self._add_horizon()

        if self.config.add_constellations:
            self._add_constellations()

        if self.config.add_constellations_names:
            self._add_constellations_names()

        # Create legend
        self._create_grouped_legend()

        return self._fig, self._ax

    def project(self, constraints: Optional[CatalogConstraints] = None):
        """
        Project astronomical objects onto the cylindrical plane.

        Args:
            constraints: Catalog constraints for star selection
        """
        # Get stars
        stars_data = self.catalog.get_stars(constraints)

        # Project stars
        self._star_projections = self._make_cylindric_projection(
            data=stars_data,
            object_type='star'
        )

        # Plot stars
        self._plot_stars(self._star_projections)

        # Add planets if requested
        if self.config.add_planets:
            planets_data = self.planets_catalog.get_planets(self.config.local_time)
            self._planets_projections = self._make_cylindric_projection(
                data=planets_data,
                object_type='planet'
            )
            self._add_planets(self._planets_projections)

    def _make_cylindric_projection(self, data: NDArray, object_type: str = 'star') -> NDArray:
        """
        Convert equatorial coordinates to cylindrical projection coordinates.

        Args:
            data: Object data with RA/Dec coordinates
            object_type: 'star' or 'planet'

        Returns:
            Structured array with projection data
        """
        PROJECTION_DTYPE = np.dtype([
            ('x', np.float32),      # RA in degrees
            ('y', np.float32),      # Dec in degrees
            ('v_mag', np.float32),  # Visual magnitude
            ('size', np.float32),   # Display size
            ('id', np.int32),       # Object ID
        ])

        # Extract coordinates
        ra = data['ra']   # Already in radians
        dec = data['dec'] # Already in radians

        # Convert to degrees for plotting
        ra_deg = np.rad2deg(ra) % 360.0
        dec_deg = np.rad2deg(dec)

        # Filter by display range
        mask = (
                (ra_deg >= self.config.ra_min) &
                (ra_deg <= self.config.ra_max) &
                (dec_deg >= self.config.dec_min) &
                (dec_deg <= self.config.dec_max)
        )

        # Create projection data
        n_visible = np.sum(mask)
        projection_data = np.zeros(n_visible, dtype=PROJECTION_DTYPE)

        projection_data['x'] = ra_deg[mask]
        projection_data['y'] = dec_deg[mask]
        projection_data['v_mag'] = data['v_mag'][mask]

        # Calculate display size based on magnitude
        projection_data['size'] = mag_to_radius(
            magnitude=projection_data['v_mag'],
            max_magnitude=self.catalog.constraints.max_magnitude,
            min_magnitude=self.catalog.constraints.min_magnitude
        )

        # Store object IDs
        if object_type == 'star':
            projection_data['id'] = data['hip_id'][mask]
        elif object_type == 'planet':
            projection_data['id'] = data['planet_id'][mask]

        return projection_data

    def _create_figure(self):
        """Create and configure the matplotlib figure."""
        if self.config.use_dark_mode:
            plt.style.use('dark_background')
            self._bg_color = 'black'
            self._grid_color = 'gray'
            self._text_color = 'white'
        else:
            plt.style.use('default')
            self._bg_color = 'white'
            self._grid_color = 'lightgray'
            self._text_color = 'black'

        self._fig, self._ax = plt.subplots(
            figsize=self.config.figsize,
            dpi=self.config.dpi
        )

        # Set limits and aspect
        self._ax.set_xlim(self.config.ra_min, self.config.ra_max)
        self._ax.set_ylim(self.config.dec_min, self.config.dec_max)

        # Labels
        self._ax.set_xlabel('Right Ascension (degrees)', fontsize=12, color=self._text_color)
        self._ax.set_ylabel('Declination (degrees)', fontsize=12, color=self._text_color)
        self._ax.set_title(
            f'Celestial Sphere - {self.config.local_time.strftime("%Y-%m-%d %H:%M")}',
            fontsize=14,
            color=self._text_color
        )

        # Background
        self._fig.patch.set_facecolor(self._bg_color)
        self._ax.set_facecolor(self._bg_color)

        #inverse x_axis
        self._ax.invert_xaxis()

    def _plot_stars(self, projection_data: NDArray):
        """
        Plot stars on the cylindrical projection.

        Args:
            projection_data: Star projection data
        """
        if len(projection_data) == 0:
            return

        x = projection_data['x']
        y = projection_data['y']
        sizes = projection_data['size'] * 3 # Scale for visibility

        color = 'white' if self.config.use_dark_mode else 'black'

        self._ax.scatter(
            x, y,
            s=sizes,
            c=color,
            alpha=0.8,
            edgecolors='none',
            zorder=2,
            label='Stars'
        )

        self._groups['Objects'] = self._groups.get('Objects', []) + [
            (self._ax.scatter([], [], c=color, s=50), 'Stars')
        ]

    def _add_planets(self, projection_data: NDArray):
        """
        Add planets to the projection.

        Args:
            projection_data: Planet projection data
        """
        if len(projection_data) == 0:
            return

        for i, planet_enum in enumerate(Planets):
            if i >= len(projection_data):
                break

            planet_data = projection_data[i]
            x = planet_data['x']
            y = planet_data['y']

            # Get planet color
            color = self.planets_catalog.get_planet_color(planet_enum)

            # Plot planet
            scatter = self._ax.scatter(
                x, y,
                s=200,
                c=color,
                edgecolors='white' if self.config.use_dark_mode else 'black',
                linewidths=1.5,
                alpha=0.9,
                zorder=5,
                label=planet_enum.name.capitalize()
            )

            # Add to legend
            self._groups['Planets'] = self._groups.get('Planets', []) + [
                (scatter, planet_enum.name.capitalize())
            ]

            # Add planet name annotation
            self._ax.annotate(
                planet_enum.name.capitalize(),
                xy=(x, y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                color=self._text_color,
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor=color,
                    alpha=0.6,
                    edgecolor='none'
                )
            )

    def _add_grid(self):
        """Add coordinate grid to the projection."""
        # RA grid lines (vertical)
        ra_lines = []
        for ra in np.arange(self.config.ra_min, self.config.ra_max + 1, self.config.grid_ra_step):
            dec_points = np.linspace(self.config.dec_min, self.config.dec_max, 100)
            ra_points = np.full_like(dec_points, ra)
            ra_lines.append(np.column_stack([ra_points, dec_points]))

        # Dec grid lines (horizontal)
        dec_lines = []
        for dec in np.arange(self.config.dec_min, self.config.dec_max + 1, self.config.grid_dec_step):
            ra_points = np.linspace(self.config.ra_min, self.config.ra_max, 100)
            dec_points = np.full_like(ra_points, dec)
            dec_lines.append(np.column_stack([ra_points, dec_points]))

        # Add grid lines
        grid_collection = LineCollection(
            ra_lines + dec_lines,
            colors=self._grid_color,
            alpha=0.3,
            linewidth=0.5,
            linestyle='--',
            zorder=1
        )
        self._ax.add_collection(grid_collection)

        self._groups['Grids'] = self._groups.get('Grids', []) + [
            (grid_collection, 'Coordinate Grid')
        ]

    def _add_ecliptic(self):
        """Add the ecliptic (path of the Sun) to the projection."""
        # The ecliptic is tilted by ~23.44 degrees relative to the celestial equator
        obliquity = 23.44  # degrees

        ra_points = np.linspace(0, 360, 1000)
        # Simplified ecliptic: dec = obliquity * sin(ra)
        dec_points = obliquity * np.sin(np.deg2rad(ra_points))

        # Filter by display range
        mask = (
                (ra_points >= self.config.ra_min) &
                (ra_points <= self.config.ra_max) &
                (dec_points >= self.config.dec_min) &
                (dec_points <= self.config.dec_max)
        )

        color = 'yellow' if self.config.use_dark_mode else 'orange'
        line, = self._ax.plot(
            ra_points[mask],
            dec_points[mask],
            color=color,
            alpha=0.7,
            linewidth=2,
            linestyle='--',
            zorder=3,
            label='Ecliptic'
        )

        self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
            (line, 'Ecliptic')
        ]

    def _add_equator(self):
        """Add the celestial equator to the projection."""
        ra_points = np.linspace(self.config.ra_min, self.config.ra_max, 1000)
        dec_points = np.zeros_like(ra_points)

        color = 'cyan' if self.config.use_dark_mode else 'blue'
        line, = self._ax.plot(
            ra_points,
            dec_points,
            color=color,
            alpha=0.7,
            linewidth=2,
            linestyle='-',
            zorder=3,
            label='Celestial Equator'
        )

        self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
            (line, 'Celestial Equator')
        ]

    def _add_galactic_equator(self):
        """Add the galactic equator to the projection."""
        # Simplified representation - actual galactic equator requires coordinate transformation
        # The galactic equator passes through RA~192°, Dec~27° (north galactic pole)

        # Generate approximate galactic equator curve
        ra_points = np.linspace(0, 360, 1000)
        # Very simplified - actual calculation requires proper coordinate transformation
        dec_points = 27 * np.sin(np.deg2rad(ra_points - 192))

        # Filter by display range
        mask = (
                (ra_points >= self.config.ra_min) &
                (ra_points <= self.config.ra_max) &
                (dec_points >= self.config.dec_min) &
                (dec_points <= self.config.dec_max)
        )

        color = 'magenta' if self.config.use_dark_mode else 'purple'
        line, = self._ax.plot(
            ra_points[mask],
            dec_points[mask],
            color=color,
            alpha=0.6,
            linewidth=1.5,
            linestyle=':',
            zorder=3,
            label='Galactic Equator (approx.)'
        )

        self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
            (line, 'Galactic Equator')
        ]

    def _add_horizon(self):
        """Add the local horizon line to the projection."""
        # This requires converting from horizontal to equatorial coordinates
        # For now, we'll add a placeholder implementation
        # TODO: Implement proper horizon calculation based on observer location and time
        pass

    def _add_constellations(self):
        """Add constellation line patterns to the projection."""
        # TODO: Implement constellation line rendering for cylindrical projection
        # This requires adapting the constellation renderer from other projections
        pass

    def _add_constellations_names(self):
        """Add constellation names to the projection."""
        if self.constellation_config.constellations_list is not None:
            constellations_to_render = self.constellation_config.constellations_list
        else:
            constellations_to_render = get_available_constellations()

        for constellation in constellations_to_render:
            center = get_constellation_center(constellation)

            # Convert from unit vector to RA/Dec
            x, y, z = center
            ra = np.arctan2(y, x)
            dec = np.arcsin(z)

            ra_deg = np.rad2deg(ra) % 360.0
            dec_deg = np.rad2deg(dec)

            # Check if in display range
            if (self.config.ra_min <= ra_deg <= self.config.ra_max and
                    self.config.dec_min <= dec_deg <= self.config.dec_max):

                self._ax.annotate(
                    constellation,
                    xy=(ra_deg, dec_deg),
                    xytext=(0, 0),
                    textcoords='offset points',
                    fontsize=10,
                    color='gray',
                    alpha=0.7,
                    ha='center',
                    va='center',
                    weight='bold'
                )

    def _create_grouped_legend(self):
        """Create a grouped legend for the visualization."""
        groups = {k: v for k, v in self._groups.items() if v}
        if not groups:
            return

        # Sort groups by size
        groups = dict(sorted(groups.items(), key=lambda x: len(x[1]), reverse=True))

        # Determine layout
        n_groups = len(groups)
        if n_groups > 3:
            n_columns = int(np.ceil(n_groups / 2))
        else:
            n_columns = n_groups

        group_items = list(groups.items())

        for i, (title, items) in enumerate(group_items):
            if not items:
                continue

            handles, labels = zip(*items)

            # Position legends
            bbox_x = 0.02 + (i % n_columns) * (0.96 / n_columns)
            bbox_y = -0.15 if i >= n_columns else -0.05

            legend = self._ax.legend(
                handles, labels,
                title=title,
                loc='upper left',
                fontsize=8,
                bbox_to_anchor=(bbox_x, bbox_y),
                frameon=True,
                fancybox=True,
                borderaxespad=0.2
            )

            legend.get_title().set_fontweight('bold')
            legend.get_title().set_fontsize(9)
            self._ax.add_artist(legend)
