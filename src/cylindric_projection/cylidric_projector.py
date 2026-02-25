"""
Module implementing cylindrical (equirectangular) projection.

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

from src.constellations_metadata.constellations_data import (
    get_available_constellations,
    get_constellation_center,
    get_constellation_lines
)
from src.helpers.geometry.geometry import mag_to_radius
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.planets_catalog.planet_catalog import PlanetCatalog, Planets


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


def _wrap_ra(ra_deg: float, ra_center: float) -> float:
    """Wrap RA value so that it is within [ra_center - 180, ra_center + 180).
    This ensures continuity of lines that cross the RA boundary.

    :param ra_deg: RA in degrees (can be any value)
    :param ra_center: Center of the RA display range in degrees
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float:
    :param ra_center: float:
    :param ra_deg: float: 
    :param ra_center: float: 
    :returns: Wrapped RA value

    """
    diff = ra_deg - ra_center
    diff = (diff + 180.0) % 360.0 - 180.0
    return ra_center + diff


def _split_segments_at_boundary(
    ra_points: NDArray,
    dec_points: NDArray,
    ra_min: float,
    ra_max: float,
    dec_min: float,
    dec_max: float,
    ra_wrap_threshold: float = 180.0
) -> List[NDArray]:
    """
    Split a continuous curve into segments, breaking at points where the curve
    jumps across the RA wrap boundary or goes out of the dec range.
    Also clips segments to the visible area, interpolating boundary crossings.

    :param ra_points: Array of RA values in degrees
    :type ra_points: NDArray
    :param dec_points: Array of Dec values in degrees
    :type dec_points: NDArray
    :param ra_min: Minimum RA of display range
    :type ra_min: float
    :param ra_max: Maximum RA of display range
    :type ra_max: float
    :param dec_min: Minimum Dec of display range
    :type dec_min: float
    :param dec_max: Maximum Dec of display range
    :type dec_max: float
    :param ra_wrap_threshold: Maximum allowed RA jump before splitting
    :type ra_wrap_threshold: float

    :return: List of Nx2 arrays, each representing a continuous segment [[ra, dec], ...]
    :rtype: List[NDArray]
    """

    if len(ra_points) < 2:
        return []

    segments = []
    current_segment = []

    for i in range(len(ra_points)):
        ra = ra_points[i]
        dec = dec_points[i]

        # Check if point is within dec range
        in_dec = dec_min <= dec <= dec_max
        # Check if point is within ra range
        in_ra = ra_min <= ra <= ra_max

        if i > 0:
            # Detect large RA jump (wrap-around)
            ra_jump = abs(ra - ra_points[i - 1])
            if ra_jump > ra_wrap_threshold:
                # Break segment here — interpolate exit and entry points
                if len(current_segment) >= 1:
                    # Interpolate the boundary crossing
                    prev_ra = ra_points[i - 1]
                    prev_dec = dec_points[i - 1]
                    curr_ra = ra
                    curr_dec = dec

                    # Determine which boundary was crossed
                    boundary_points = _interpolate_ra_wrap(
                        prev_ra, prev_dec, curr_ra, curr_dec,
                        ra_min, ra_max
                    )

                    if boundary_points is not None:
                        exit_ra, exit_dec, entry_ra, entry_dec = boundary_points

                        # Add exit point to current segment
                        if dec_min <= exit_dec <= dec_max:
                            current_segment.append([exit_ra, exit_dec])

                        # Finalize current segment
                        if len(current_segment) >= 2:
                            segments.append(np.array(current_segment))
                        current_segment = []

                        # Start new segment with entry point
                        if dec_min <= entry_dec <= dec_max:
                            current_segment.append([entry_ra, entry_dec])
                    else:
                        if len(current_segment) >= 2:
                            segments.append(np.array(current_segment))
                        current_segment = []
                else:
                    current_segment = []

                # Add current point if in range
                if in_dec and in_ra:
                    current_segment.append([ra, dec])
                continue

        if in_dec and in_ra:
            if len(current_segment) == 0 and i > 0:
                # Interpolate entry from out-of-range to in-range
                prev_ra = ra_points[i - 1]
                prev_dec = dec_points[i - 1]
                edge_point = _interpolate_dec_boundary(
                    prev_ra, prev_dec, ra, dec, dec_min, dec_max
                )
                if edge_point is not None:
                    current_segment.append(edge_point)

            current_segment.append([ra, dec])
        else:
            if len(current_segment) >= 1:
                # Interpolate exit point
                prev_ra = ra_points[i - 1] if i > 0 else ra
                prev_dec = dec_points[i - 1] if i > 0 else dec
                if len(current_segment) > 0:
                    prev_ra = current_segment[-1][0]
                    prev_dec = current_segment[-1][1]
                edge_point = _interpolate_dec_boundary(
                    prev_ra, prev_dec, ra, dec, dec_min, dec_max
                )
                if edge_point is not None:
                    current_segment.append(edge_point)

                if len(current_segment) >= 2:
                    segments.append(np.array(current_segment))
                current_segment = []

    # Finalize last segment
    if len(current_segment) >= 2:
        segments.append(np.array(current_segment))

    return segments


def _interpolate_ra_wrap(
    ra1: float, dec1: float,
    ra2: float, dec2: float,
    ra_min: float, ra_max: float
) -> Optional[Tuple[float, float, float, float]]:
    """Interpolate the point where a line segment crosses the RA wrap boundary.

    :param ra1: Right ascension of the start point
    :type ra1: float
    :param dec1: Declination of the start point
    :type dec1: float
    :param ra2: Right ascension of the end point
    :type ra2: float
    :param dec2: Declination of the end point
    :type dec1: float
    :param ra_min: Right ascension low boundary
    :type ra_min: float
    :param ra_max: Right ascension high boundary
    :type ra_max: float

    :return: interpolation result in format Tuple (exit_ra, exit_dec, entry_ra, entry_dec)
    :rtype: Tuple[float, float, float, float] | None
    """

    # Determine direction of wrap
    if ra1 > ra2:
        # Wrapping from high RA to low RA (crossing ra_max -> ra_min)
        # The "real" ra2 is ra2 + 360
        ra2_unwrapped = ra2 + 360.0
        # Fraction along segment where RA = ra_max
        if abs(ra2_unwrapped - ra1) < 1e-10:
            return None
        t = (ra_max - ra1) / (ra2_unwrapped - ra1)
        t = np.clip(t, 0, 1)
        dec_at_boundary = dec1 + t * (dec2 - dec1)
        return ra_max, dec_at_boundary, ra_min, dec_at_boundary
    else:
        # Wrapping from low RA to high RA (crossing ra_min -> ra_max)
        ra1_unwrapped = ra1 + 360.0
        if abs(ra1_unwrapped - ra2) < 1e-10:
            return None
        t = (ra_max - ra2) / (ra1_unwrapped - ra2)
        t = np.clip(t, 0, 1)
        dec_at_boundary = dec2 + t * (dec1 - dec2)
        return ra_min, dec_at_boundary, ra_max, dec_at_boundary


def _interpolate_dec_boundary(
    ra1: float, dec1: float,
    ra2: float, dec2: float,
    dec_min: float, dec_max: float
) -> Optional[List[float]]:
    """Linear interpolation the point where a line crosses a dec boundary.

        :param ra1: Right ascension of the start point
    :type ra1: float
    :param dec1: Declination of the start point
    :type dec1: float
    :param ra2: Right ascension of the end point
    :type ra2: float
    :param dec2: Declination of the end point
    :type dec1: float
    :param dec_min: Declination low boundary
    :type dec_min: float
    :param dec_max: Declination high boundary
    :type dec_max: float

    :return: interpolation result in format [ra, dec] -- intersection point
    :rtype: List[float] | None

    """
    if abs(dec2 - dec1) < 1e-10:
        return None

    # Check which boundary is crossed
    for boundary in [dec_min, dec_max]:
        t = (boundary - dec1) / (dec2 - dec1)
        if 0.0 <= t <= 1.0:
            ra_at_boundary = ra1 + t * (ra2 - ra1)
            return [ra_at_boundary, boundary]

    return None


def _make_pair_segments_with_wrapping(
    ra1: float, dec1: float,
    ra2: float, dec2: float,
    ra_min: float, ra_max: float,
    ra_wrap_threshold: float = 180.0
) -> List[NDArray]:
    """Create line segments for a pair of points, handling RA wrap-around.
    If the RA difference is larger than the threshold, splits into two segments
    that go to opposite edges of the frame.

    :param ra1: Right ascension of the first point
    :type ra1: float
    :param dec1: Declination of the first point
    :type dec1: float
    :param ra2: Right ascension of the second point
    :type ra2: float
    :param dec2: Declination of the second point
    :type dec1: float
    :param ra_min: Right ascension low boundary
    :type ra_min: float
    :param ra_max: Right ascension high boundary
    :type ra_max: float
    :param ra_wrap_threshold: Maximum allowed RA difference
    :type ra_wrap_threshold: float (Default value = 180.0)

    :return: List of Nx2 arrays representing line segments
    :rtype: List[NDArray]
    """
    ra_diff = abs(ra2 - ra1)

    if ra_diff <= ra_wrap_threshold:
        # No wrapping needed — single segment
        return [np.array([[ra1, dec1], [ra2, dec2]])]

    # Wrapping needed — split into two segments
    boundary_points = _interpolate_ra_wrap(ra1, dec1, ra2, dec2, ra_min, ra_max)
    if boundary_points is None:
        return [np.array([[ra1, dec1], [ra2, dec2]])]

    exit_ra, exit_dec, entry_ra, entry_dec = boundary_points

    segments = [
        np.array([[ra1, dec1], [exit_ra, exit_dec]]),   # Segment from point1 to exit boundary
        np.array([[entry_ra, entry_dec], [ra2, dec2]])  # Segment from entry boundary to point2
    ]

    return segments


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

        :param config: Projection configuration
        :type config: CylindricConfig
        :param catalog: Star catalog instance
        :type catalog: Catalog
        :param planets_catalog: Planet catalog instance
        :type planets_catalog: PlanetCatalog
        :param constellation_config: Constellation rendering configuration
        :type constellation_config: ConstellationConfig
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

    @property
    def _ra_center(self) -> float:
        """Center of the RA display range."""
        return (self.config.ra_min + self.config.ra_max) / 2.0

    @property
    def _ra_span(self) -> float:
        """Span of the RA display range."""
        return self.config.ra_max - self.config.ra_min

    def generate(self, constraints: Optional[CatalogConstraints] = None) -> Tuple[plt.Figure, plt.Axes]:
        """Generate a cylindrical projection visualization.

        :param constraints: Catalog constraints for star selection
        :type constraints: Optional[CatalogConstraints]:  (Default value = None)
        :return: Tuple of (figure, axes)
        :rtype: Tuple[plt.Figure, plt.Axes]
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
        # self._create_grouped_legend()

        return self._fig, self._ax

    def project(self, constraints: Optional[CatalogConstraints] = None):
        """Project astronomical objects onto the cylindrical plane.

        :param constraints: Catalog constraints for star selection
        :type constraints: Optional[CatalogConstraints]:  (Default value = None)
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
        """Convert equatorial coordinates to cylindrical projection coordinates.

        :param data: Object data with RA/Dec coordinates
        :type data: NDArray
        :param object_type: star' or 'planet'
        :type object_type: str:  (Default value = 'star')

        :return: Structured array with projection data
        :rtype: NDArray
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
        import matplotlib
        matplotlib.rcdefaults()

        if self.config.use_dark_mode:
            self._bg_color   = 'black'
            self._grid_color = 'gray'
            self._text_color = 'white'
        else:
            self._bg_color   = 'white'
            self._grid_color = 'lightgray'
            self._text_color = 'black'

        self._fig, self._ax = plt.subplots(
            figsize=self.config.figsize,
            dpi=self.config.dpi
        )

        # Явно устанавливаем цвета только для этой фигуры
        self._fig.patch.set_facecolor(self._bg_color)
        self._ax.set_facecolor(self._bg_color)

        # Labels
        self._ax.set_xlim(self.config.ra_min, self.config.ra_max)
        self._ax.set_ylim(self.config.dec_min, self.config.dec_max)
        self._ax.set_xlabel('Right Ascension (degrees)', fontsize=12, color=self._text_color)
        self._ax.set_ylabel('Declination (degrees)', fontsize=12, color=self._text_color)
        self._ax.set_title(
            f'Celestial Sphere - {self.config.local_time.strftime("%Y-%m-%d %H:%M")}',
            fontsize=14,
            color=self._text_color
        )
        self._ax.tick_params(colors=self._text_color)
        self._ax.spines[:].set_color(self._text_color)
        self._ax.invert_xaxis()

    def _plot_stars(self, projection_data: NDArray):
        """Plot stars on the cylindrical projection.

        :param projection_data: Star projection data
        :type projection_data: NDArray
        """

        if len(projection_data) == 0:
            return

        x = projection_data['x']
        y = projection_data['y']
        sizes = projection_data['size'] * 3  # Scale for visibility

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
        """Add planets to the projection.

        :param projection_data: Planet projection data
        :type projection_data: NDArray
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

    def _plot_curve_with_wrapping(
        self,
        ra_points: NDArray,
        dec_points: NDArray,
        color: str,
        alpha: float = 0.7,
        linewidth: float = 2.0,
        linestyle: str = '--',
        zorder: int = 3,
        label: str = ''
    ) -> Optional[LineCollection]:
        """Plot a curve on the cylindrical projection, correctly handling
        RA wrap-around and dec boundary clipping.

        :param ra_points: RA values in degrees (full 0..360 range)
        :type ra_points: NDArray
        :param dec_points: Dec values in degrees
        :type dec_points: NDArray
        :param color: Line color
        :type color: str
        :param alpha: Line transparency
        :type alpha: float:  (Default value = 0.7)
        :param linewidth: Line width
        :type linewidth: float:  (Default value = 2.0)
        :param linestyle: Line style
        :type linestyle: str:  (Default value = '--')
        :param zorder: Drawing order
        :type zorder: int:  (Default value = 3)
        :param label: Legend label
        :type label: str:  (Default value = '')

        :return: curves
        :rtype: LineCollection | None
        """
        segments = _split_segments_at_boundary(
            ra_points, dec_points,
            self.config.ra_min, self.config.ra_max,
            self.config.dec_min, self.config.dec_max,
            ra_wrap_threshold=self._ra_span * 0.5
        )

        if not segments:
            return None

        collection = LineCollection(
            segments,
            colors=color,
            alpha=alpha,
            linewidths=linewidth,
            linestyle=linestyle,
            zorder=zorder,
            label=label
        )
        self._ax.add_collection(collection)
        return collection

    def _add_ecliptic(self):
        """Add the ecliptic to the projection."""

        obliquity = 23.44  # degrees

        ra_points = np.linspace(0, 360, 1000)
        dec_points = obliquity * np.sin(np.deg2rad(ra_points))

        color = 'yellow' if self.config.use_dark_mode else 'orange'

        collection = self._plot_curve_with_wrapping(
            ra_points, dec_points,
            color=color,
            alpha=0.7,
            linewidth=2,
            linestyle='--',
            zorder=3,
            label='Ecliptic'
        )

        if collection:
            self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
                (collection, 'Ecliptic')
            ]

    def _add_equator(self):
        """Add the celestial equator to the projection."""

        ra_points = np.linspace(self.config.ra_min, self.config.ra_max, 1000)
        dec_points = np.zeros_like(ra_points)

        color = 'cyan' if self.config.use_dark_mode else 'blue'

        collection = self._plot_curve_with_wrapping(
            ra_points, dec_points,
            color=color,
            alpha=0.7,
            linewidth=2,
            linestyle='-',
            zorder=3,
            label='Celestial Equator'
        )

        if collection:
            self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
                (collection, 'Celestial Equator')
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

        from src.helpers.time.time import vequinox_hour_angle

        # Calculate local sidereal time
        sidereal_time = vequinox_hour_angle(
            longitude=self.config.longitude,
            local=self.config.local_time
        )

        # Generate azimuth points for horizon circle
        num_points = 1000
        azimuth_points = np.linspace(0, 2 * np.pi, num_points)

        sin_lat = np.sin(self.config.latitude)
        cos_lat = np.cos(self.config.latitude)

        # Vectorized computation
        sin_az = np.sin(azimuth_points)
        cos_az = np.cos(azimuth_points)

        # At horizon (altitude = 0):
        # sin(dec) = cos(lat) * cos(az)
        sin_dec = cos_lat * cos_az
        dec = np.arcsin(np.clip(sin_dec, -1, 1))

        # Hour angle: H = atan2(sin(az), cos(az) * sin(lat))
        H = np.arctan2(sin_az, cos_az * sin_lat)

        # RA = LST - H
        ra = (sidereal_time - H) % (2 * np.pi)

        ra_deg = np.rad2deg(ra) % 360.0
        dec_deg = np.rad2deg(dec)

        # Sort by RA for cleaner plotting
        sort_idx = np.argsort(ra_deg)
        ra_deg = ra_deg[sort_idx]
        dec_deg = dec_deg[sort_idx]

        color = 'lime' if self.config.use_dark_mode else 'green'

        collection = self._plot_curve_with_wrapping(
            ra_deg, dec_deg,
            color=color,
            alpha=0.6,
            linewidth=2,
            linestyle='-.',
            zorder=3,
            label='Horizon'
        )

        if collection:
            self._groups['Reference Lines'] = self._groups.get('Reference Lines', []) + [
                (collection, 'Horizon')
            ]

    def _add_constellations(self):
        """Add constellation line patterns to the projection."""

        # Determine which constellations to render
        if self.constellation_config.constellations_list is not None:
            constellations_to_render = self.constellation_config.constellations_list
        else:
            constellations_to_render = get_available_constellations()

        # Get all star data for constellation line matching
        stars_data = self.catalog.data

        # Create a mapping from HIP ID to star coordinates in degrees
        hip_to_star = {}
        for star in stars_data:
            hip_id = star['hip_id']
            ra_deg = np.rad2deg(star['ra']) % 360.0
            dec_deg = np.rad2deg(star['dec'])
            hip_to_star[hip_id] = (ra_deg, dec_deg)

        # Process each constellation
        all_segments = []

        for constellation in constellations_to_render:
            try:
                # Get constellation line data
                lines = get_constellation_lines(constellation)

                if not lines:
                    continue

                # Get color for this constellation
                if (self.constellation_config.constellation_color_map and
                        constellation in self.constellation_config.constellation_color_map):
                    color = self.constellation_config.constellation_color_map[constellation]
                else:
                    color = self.constellation_config.constellation_color

                # Process each line (chain of stars) in the constellation
                for line in lines:
                    # Get coordinates for each star in the chain
                    chain_points = []
                    for hip_id in line:
                        if hip_id in hip_to_star:
                            ra_deg, dec_deg = hip_to_star[hip_id]
                            chain_points.append((ra_deg, dec_deg))
                        else:
                            # Star not found — break the chain
                            if len(chain_points) >= 2:
                                # Process the chain we have so far
                                self._add_constellation_chain(chain_points, all_segments)
                            chain_points = []

                    # Process remaining chain
                    if len(chain_points) >= 2:
                        self._add_constellation_chain(chain_points, all_segments)

            except Exception as e:
                print(f"Warning: Could not render constellation {constellation}: {e}")
                continue

        # Create LineCollection for all constellation segments
        if all_segments:
            constellation_collection = LineCollection(
                all_segments,
                colors=self.constellation_config.constellation_color,
                alpha=self.constellation_config.constellation_alpha,
                linewidths=self.constellation_config.constellation_linewidth,
                zorder=4,
                label='Constellations'
            )
            self._ax.add_collection(constellation_collection)

            self._groups['Constellations'] = self._groups.get('Constellations', []) + [
                (constellation_collection, 'Constellation Lines')
            ]

    def _add_constellation_chain(
        self,
        chain_points: List[Tuple[float, float]],
        all_segments: List[NDArray]
    ):
        """Process a chain of constellation stars into line segments,
        handling RA wrap-around correctly.

        :param chain_points: List of (ra_deg, dec_deg) tuples
        :type chain_points: List[Tuple[float, float]]
        :param all_segments: List to append resulting segments to
        :type all_segments: List[NDArray]
        """
        for i in range(len(chain_points) - 1):
            ra1, dec1 = chain_points[i]
            ra2, dec2 = chain_points[i + 1]

            # Check if both points are within dec range
            # (we still want to draw partial segments if one point is outside)
            dec_ok_1 = self.config.dec_min <= dec1 <= self.config.dec_max
            dec_ok_2 = self.config.dec_min <= dec2 <= self.config.dec_max

            if not dec_ok_1 and not dec_ok_2:
                continue

            # Handle RA wrap-around for this pair
            pair_segments = _make_pair_segments_with_wrapping(
                ra1, dec1, ra2, dec2,
                self.config.ra_min, self.config.ra_max,
                ra_wrap_threshold=self._ra_span * 0.5
            )

            for seg in pair_segments:
                # Clip each segment to display range
                clipped = self._clip_segment_to_range(seg)
                if clipped is not None and len(clipped) >= 2:
                    all_segments.append(clipped)

    def _clip_segment_to_range(self, segment: NDArray) -> Optional[NDArray]:
        """Clip a 2-point segment to the display range, interpolating at boundaries.

        :param segment: Nx2 array of [ra, dec] points
        :type segment: NDArray

        :return: Clipped segment or None if entirely outside
        :rtype: Optional[NDArray]
        """

        if len(segment) < 2:
            return None

        clipped_points = []

        for i in range(len(segment)):
            ra, dec = segment[i]
            in_range = (
                self.config.ra_min <= ra <= self.config.ra_max and
                self.config.dec_min <= dec <= self.config.dec_max
            )

            if i > 0:
                prev_ra, prev_dec = segment[i - 1]
                prev_in_range = (
                    self.config.ra_min <= prev_ra <= self.config.ra_max and
                    self.config.dec_min <= prev_dec <= self.config.dec_max
                )

                # Handle transitions in/out of range
                if in_range and not prev_in_range:
                    # Entering the range — add boundary point
                    edge = _interpolate_dec_boundary(
                        prev_ra, prev_dec, ra, dec,
                        self.config.dec_min, self.config.dec_max
                    )
                    if edge:
                        clipped_points.append(edge)
                elif not in_range and prev_in_range:
                    # Leaving the range — add boundary point
                    edge = _interpolate_dec_boundary(
                        prev_ra, prev_dec, ra, dec,
                        self.config.dec_min, self.config.dec_max
                    )
                    if edge:
                        clipped_points.append(edge)
                    continue

            if in_range:
                clipped_points.append([ra, dec])

        if len(clipped_points) >= 2:
            return np.array(clipped_points)
        return None

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
            dec = np.arcsin(np.clip(z, -1, 1))

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