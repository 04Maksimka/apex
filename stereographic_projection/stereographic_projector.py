"""Module implementing main stereographic projection."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from numpy.typing import NDArray
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

from helpers.geometry import (
    get_horizontal_coords, make_projections, make_circle_projection, generate_small_circle,
)
from hip_catalog.hip_catalog import CatalogConstraints, Catalog
from planets_catalog.planet_catalog import PlanetCatalog, Planets
from matplotlib.collections import LineCollection


@dataclass
class StereoProjConfig(object):
    """Class of configuration of the StereoProjector."""

    local_time: datetime
    latitude: float = 0.0
    longitude: float = 0.0
    grid_theta_step: float = 10.0
    grid_phi_step: float = 10.0

    # Flags
    add_ecliptic: bool = False
    add_equator: bool = False
    add_galactic_equator: bool = False
    add_planets: bool = False
    add_ticks: bool = False
    add_horizontal_grid: bool = False
    add_equatorial_grid: bool = False
    random_origin: bool = False

    def __post_init__(self):
        # Store in radians
        self.latitude = np.deg2rad(self.latitude)
        self.longitude = np.deg2rad(self.longitude)


class StereoProjector(object):
    """Class of the stereographic projector."""

    catalog: Catalog       # Star catalog
    planets_catalog: PlanetCatalog
    config: StereoProjConfig    # Stereo projector configuration
    _fig: plt.Figure            # Skychart figure
    _ax: plt.Axes               # Skychart axes

    def __init__(self, config: StereoProjConfig, catalog: Catalog, planets_catalog: PlanetCatalog):
        self.config = config
        self.catalog = catalog
        self.planets_catalog = planets_catalog

    def generate(self, constraints: Optional[CatalogConstraints]=None) -> plt.Figure:
        """
        Generate a projection.

        :return: figure
        """

        # Get catalog
        _ = self.catalog.get_stars(constraints)

        # From equatorial to horizontal
        star_view_data = self._make_horizontal_views(
            data=self.catalog.data,
            object_type='star'
        )
        # Make projections
        points_data = make_projections(
            view_data=star_view_data,
            constraints=self.catalog.constraints,
        )
        # Make figure with projections
        self._create_polar_scatter(points_data)

        # Add ecliptic
        if self.config.add_ecliptic:
            self._add_ecliptic()

        # Add equator
        if self.config.add_equator:
            self._add_equator()

        # Add galactic equator
        if self.config.add_galactic_equator:
            self._add_galactic_equator()

        # Add horizontal grid
        if self.config.add_horizontal_grid:
            self._add_horizontal_grid()

        # Add equatorial grid
        if self.config.add_equatorial_grid:
            self._add_equatorial_grid()

        # Add planets
        if self.config.add_planets:
            planet_data = self.planets_catalog.get_planets(self.config.local_time)
            planet_view_data = self._make_horizontal_views(
                data=planet_data,
                object_type='planet'
            )
            planet_points_data = make_projections(
                view_data=planet_view_data,
                constraints=self.catalog.constraints,
            )
            self._add_planets(planet_points_data)

        # Put a legend to the bottom of the current axis
        box = self._ax.get_position()
        self._ax.set_position((box.x0, box.y0, box.width * 0.8, box.height))
        if self._ax.get_legend_handles_labels()[1]:
            self._ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=5)

        return self._fig

    def _make_horizontal_views(self, data: NDArray, object_type: str = 'star') -> NDArray:
        """
        Returns horizontal coordinates.

        :param data: objects equatorial coordinates
        :param object_type: star or planet
        :return: view parameters
        """
        VIEW_DTYPE = np.dtype([
            ('v_mag', np.float32),
            ('zenith', np.float32),
            ('azimuth', np.float32),
            ('id', np.int32),
        ])

        horizontal_coords = get_horizontal_coords(self.config.__dict__, data=data)

        number_of_stars = data.shape[0]
        view_data = np.zeros(number_of_stars, dtype=VIEW_DTYPE)
        view_data['v_mag'] = data['v_mag']
        view_data['zenith'] = horizontal_coords['zenith']
        view_data['azimuth'] = horizontal_coords['azimuth']

        if object_type == 'star':
            view_data['id'] = data['hip_id']
        elif object_type == 'planet':
            view_data['id'] = data['planet_id']

        return view_data

    def _add_ecliptic(self):
        """
        Add ecliptic on skychart
        """

        RA = 270.0
        DEC = 66.5607

        ecliptic_eci_coords = generate_small_circle(
            spheric_normal=np.array([90.0 - DEC, RA]),
            alpha=90.0,
            num_points=1000
        )
        horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=ecliptic_eci_coords
        )
        projection_coords = make_circle_projection(
            azimuths=horizontal_coords['azimuth'],
            zeniths=horizontal_coords['zenith']
        )
        self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='green',
            linewidth=1,
            label='Ecliptic',
        )

    def _add_equator(self):
        """
        Add celestial equator on skychart
        """

        equator_eci_coords = generate_small_circle(
            spheric_normal=np.array([0.0, 0.0]),
            alpha=90.0,
            num_points=1000
        )

        horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=equator_eci_coords
        )
        projection_coords = make_circle_projection(
            azimuths=horizontal_coords['azimuth'],
            zeniths=horizontal_coords['zenith']
        )
        self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='red',
            linewidth=1,
            label='Equator',
        )

    def _add_galactic_equator(self):
        """
        Add galactic equator on skychart
        """

        RA = 192.85948
        DEC = 27.12825

        galactic_eci_coords = generate_small_circle(
            spheric_normal=np.array([90.0 - DEC, RA]),
            alpha=90.0,
            num_points=1000
        )

        horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=galactic_eci_coords
        )
        projection_coords = make_circle_projection(
            azimuths=horizontal_coords['azimuth'],
            zeniths=horizontal_coords['zenith']
        )
        self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='blue',
            linewidth=1,
            label='Galactic equator'
        )

    def _add_planets(self, projection_data: NDArray):
        """
        Add planets to the scatter plot.

        :param projection_data: projection points for planets
        """
        for planet_data in projection_data:
            planet = Planets(planet_data['id'])
            name = planet.name.capitalize()
            color = self.planets_catalog.get_planet_color(planet)
            self._ax.scatter(
                planet_data['angle'],
                planet_data['radius'],
                c=color,
                s=max(planet_data['size'] * 3, 0.5),  # make planets larger for visibility
                alpha=0.8,
                linewidth=0.5,
                label=name,
            )

    def _add_horizontal_grid(self):
        """
        Add horizontal grid to skychart
        """
        zeniths = np.arange(-90.0, 90.0, self.config.grid_theta_step, dtype=np.float64)
        azimuths = np.arange(0, 180.0, self.config.grid_phi_step, dtype=np.float64)

        array_grid = []

        for azimuth in azimuths:
            circle = generate_small_circle(
                spheric_normal=np.array([90.0, azimuth + 90.0]),
                alpha=90.0,
                num_points=100,
            )
            projection = make_circle_projection(
                azimuths=circle['phi'],
                zeniths=circle['theta'],
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )

        for zenith in zeniths:
            circle = generate_small_circle(
                spheric_normal=np.array([0.0, 0.0]),
                alpha=zenith,
                num_points=100,
            )
            projection = make_circle_projection(
                azimuths=circle['phi'],
                zeniths=circle['theta'],
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )

        grid = LineCollection(
            segments=array_grid,
            label='Azimuthal grid',
            colors='olive',
            alpha=0.25,
            linewidth=0.5
        )
        self._ax.add_collection(grid)

    def _add_equatorial_grid(self):
        """
        Add equatorial grid to skychart
        """

        declinations = np.arange(-90.0, 90.0, self.config.grid_theta_step, dtype=np.float64)
        right_ascensions = np.arange(0, 180.0, self.config.grid_phi_step, dtype=np.float64)

        array_grid = []

        for ra in right_ascensions:
            eq_circle = generate_small_circle(
                spheric_normal=np.array([90.0, ra + 90.0]),
                alpha=90.0,
                num_points=100,
            )
            horizontal_coords = get_horizontal_coords(
                config=self.config.__dict__,
                data=eq_circle,
            )
            projection = make_circle_projection(
                azimuths=horizontal_coords['azimuth'],
                zeniths=horizontal_coords['zenith'],
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )

        for dec in declinations:
            eq_circle = generate_small_circle(
                spheric_normal=np.array([0.0, 0.0]),
                alpha=(90.0 - dec),
                num_points=100,
            )
            horizontal_coords = get_horizontal_coords(
                config=self.config.__dict__,
                data=eq_circle,
            )
            projection = make_circle_projection(
                azimuths=horizontal_coords['azimuth'],
                zeniths=horizontal_coords['zenith'],
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )

        grid = LineCollection(array_grid, label='Equatorial grid',
                              colors='magenta', alpha=0.25, linewidth=0.5)
        self._ax.add_collection(grid)

    def _create_polar_scatter(self, projection_data: NDArray):
        """
        Create a scatter plot in polar coordinates for stars.

        :param projection_data: projection points to place on figure
        """

        # Set up the figure with polar projection
        self._fig = plt.figure()
        self._ax = self._fig.add_subplot(111, projection='polar')

        # Get parameters from projections data array
        sizes = projection_data['size']
        angles = projection_data['angle']
        radii = projection_data['radius']

        # Make scatter
        self._ax.scatter(
            angles,
            radii,
            c='black',
            s=sizes,
            alpha=1,
            linewidth=0.5,
        )

        # Randomize north direction
        if self.config.random_origin:
            self._ax.set_theta_offset(np.random.uniform(-np.pi, +np.pi))
        else:
            self._ax.set_theta_offset(-np.pi / 2)

        # Add ticks if needed
        if self.config.add_ticks:
            angles_deg = [0, 90, 180, 270]
            angles_rad = np.deg2rad(angles_deg)
            cardinal_labels = ['S', 'W', 'N', 'E']

            self._ax.set_xticks(angles_rad)
            self._ax.set_xticklabels(cardinal_labels, fontsize=12, fontweight='bold')

            minor_angles_deg = np.arange(0, 360, 30)
            minor_angles_rad = np.deg2rad(minor_angles_deg)
            numeric_labels = [f'{angle}°' for angle in minor_angles_deg]

            self._ax.set_xticks(minor_angles_rad, minor=True)
            self._ax.set_xticklabels(numeric_labels, minor=True, fontsize=9)

            # Configure minor (numerical) ticks
            for tick in self._ax.xaxis.get_minor_ticks():
                tick.tick2line.set_visible(True)
                tick.tick2line.set_markersize(1)
                tick.tick2line.set_markeredgewidth(0.5)
            # Configure major (literal NESW) ticks
            for tick in self._ax.xaxis.get_major_ticks():
                tick.tick2line.set_visible(True)
                tick.tick2line.set_markersize(3)
                tick.tick2line.set_markeredgewidth(1)
        else:
            self._ax.set_xticks([])

        # Add circle around skychart
        r_max = self._ax.get_rmax()
        circle = Circle((0, 0), r_max,
                        transform=self._ax.transData._b,
                        fill=False,
                        edgecolor='black',
                        linewidth=1,
                        alpha=1.0,
                        zorder=10)  # поверх всего

        self._ax.add_patch(circle)

        self._ax.xaxis.grid(False)
        self._ax.set_yticks([])
        self._ax.set_ylim((0.0, 2.0))
