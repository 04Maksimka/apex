"""Module implementing main stereographic projection."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from numpy.typing import NDArray
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

from helpers.geometry.geometry import (
    get_horizontal_coords, make_stereo_projection, make_points_stereo_projection, generate_small_circle,
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
    add_zenith: bool = False
    add_poles: bool = False
    random_origin: bool = False

    def __post_init__(self):
        # Store in radians
        self.latitude = np.deg2rad(self.latitude)
        self.longitude = np.deg2rad(self.longitude)


class StereoProjector(object):
    """Class of the stereographic projector."""

    def __init__(
        self,
        config: StereoProjConfig,
        catalog: Catalog,
        planets_catalog: PlanetCatalog,
        random_angle: float = np.random.uniform(0.0, 2*np.pi)
    ):
        self.config = config
        self.catalog = catalog
        self.planets_catalog = planets_catalog
        self.random_angle = random_angle
        self._groups = {}  # Legend groups - initialize as instance variable

    def generate(self, constraints: Optional[CatalogConstraints]=None) -> plt.Figure:
        """
        Generate a stereographic projection image.

        :param constraints: Catalog constraints
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
        points_data = make_stereo_projection(
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

        if self.config.add_zenith:
            self._add_zenith()

        if self.config.add_poles:
            self._add_poles()

        # Add planets
        if self.config.add_planets:
            planet_data = self.planets_catalog.get_planets(self.config.local_time)
            planet_view_data = self._make_horizontal_views(
                data=planet_data,
                object_type='planet'
            )
            planet_points_data = make_stereo_projection(
                view_data=planet_view_data,
                constraints=self.catalog.constraints,
            )
            self._add_planets(planet_points_data)

        # Put a legend to the bottom of the current axis
        self._create_grouped_legend()

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

        valid_mask, horizontal_coords = get_horizontal_coords(self.config.__dict__, data=data)

        view_data = np.zeros(np.sum(valid_mask), dtype=VIEW_DTYPE)
        view_data['v_mag'] = data['v_mag'][valid_mask]
        view_data['zenith'] = horizontal_coords['zenith'][valid_mask]
        view_data['azimuth'] = horizontal_coords['azimuth'][valid_mask]

        if object_type == 'star':
            view_data['id'] = data['hip_id'][valid_mask]
        elif object_type == 'planet':
            view_data['id'] = data['planet_id'][valid_mask]

        return view_data

    def _add_zenith(self):
        point = self._ax.scatter(
            x=0,
            y=0,
            c='red',
            sizes=[5],
        )
        self._ax.annotate(
            'Z',
            xy=(0, 0),
            xytext=(3, 3),
            fontsize=14,
            textcoords='offset points',
            color='black',
            fontweight='bold'
        )
        self._groups['Points'] = self._groups.get('Points', []) + [(point, 'Zenith')]

    def _add_poles(self):
        POINT_DTYPE = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        north_pole = np.array([(0, 0, 1)], dtype=POINT_DTYPE)
        south_pole = np.array([(0, 0, -1)], dtype=POINT_DTYPE)

        _, north_horizontal = get_horizontal_coords(
            config=self.config.__dict__,
            data=north_pole
        )
        if north_horizontal['zenith'] < np.pi / 2:
            north_projection = make_points_stereo_projection(
                points=north_horizontal
            )
            print(north_projection)
            north = self._ax.scatter(
                north_projection['angle'],
                north_projection['radius'],
                c='blue',
                s=5,
            )
            self._ax.annotate(
                text='P',
                xy=(north_projection['angle'][0], north_projection['radius'][0]),
                xytext=(3, -10),
                fontsize=14,
                textcoords='offset points',
                color='black',
                fontweight='bold'
            )
            self._groups['Points'] = self._groups.get('Points', []) + [(north, 'North Pole')]

        _, south_horizontal = get_horizontal_coords(
            config=self.config.__dict__,
            data=south_pole
        )

        if south_horizontal['zenith'] < np.pi / 2:
            south_projection = make_points_stereo_projection(
                points=south_horizontal
            )
            south = self._ax.scatter(
                south_projection['angle'],
                south_projection['radius'],
                c='blue',
                s=5,
            )
            self._ax.annotate(
                text='P',
                xy=(south_projection['angle'][0], south_projection['radius'][0]),
                xytext=(3, -10),
                fontsize=14,
                textcoords='offset points',
                color='black',
                fontweight='bold'
            )
            self._groups['Points'] = self._groups.get('Points', []) + [(south, 'South Pole')]

    def _add_ecliptic(self):
        """
        Add ecliptic on skychart
        """

        RA = 270.0
        DEC = 66.5607

        ecliptic_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([90.0 - DEC, RA]),
            alpha_deg=90.0,
            num_points=1000
        )
        _, horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=ecliptic_eci_coords
        )
        projection_coords = make_points_stereo_projection(
            points=horizontal_coords
        )
        line, = self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='green',
            linewidth=1,
        )
        # Add to the legend groups
        self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Ecliptic')]

    def _add_equator(self):
        """
        Add celestial equator on skychart
        """

        equator_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([0.0, 0.0]),
            alpha_deg=90.0,
            num_points=1000
        )
        _, horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=equator_eci_coords
        )
        projection_coords = make_points_stereo_projection(
            points=horizontal_coords
        )
        line, = self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='red',
            linewidth=1,
        )
        # Add to the legend groups
        self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Celestial equator')]

    def _add_galactic_equator(self):
        """
        Add galactic equator on skychart
        """

        # Galactical center
        RA = 192.85948
        DEC = 27.12825

        galactic_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([90.0 - DEC, RA]),
            alpha_deg=90.0,
            num_points=1000
        )
        _, horizontal_coords = get_horizontal_coords(
            config=self.config.__dict__,
            data=galactic_eci_coords
        )
        projection_coords = make_points_stereo_projection(
            points=horizontal_coords
        )
        line, = self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='blue',
            linewidth=1,
        )
        # Add to the legend groups
        self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Galactic equator')]

    def _add_planets(self, projection_data: NDArray):
        """
        Add planets to the scatter plot.

        :param projection_data: projection points for planets
        """
        # Draw each planet separately
        for planet_data in projection_data:
            planet = Planets(planet_data['id'])
            name = planet.name.capitalize()
            color = self.planets_catalog.get_planet_color(planet)
            scatter = self._ax.scatter(
                planet_data['angle'],
                planet_data['radius'],
                c=color,
                s=max(planet_data['size'] * 3, 0.5),  # make planets larger for visibility
                alpha=0.8,
                linewidth=0.5,
            )
            # Add to the legend groups
            self._groups['Planets'] = self._groups.get('Planets', []) + [(scatter, name)]

    def _add_horizontal_grid(self):
        """
        Add horizontal grid to skychart
        """
        zeniths = np.arange(-90.0, 90.0, self.config.grid_theta_step, dtype=np.float64)
        azimuths = np.arange(0, 180.0, self.config.grid_phi_step, dtype=np.float64)

        array_grid = []

        # Draw azimuthal great circles
        for azimuth in azimuths:
            circle = generate_small_circle(
                spheric_normal_deg=np.array([90.0, azimuth + 90.0]),
                alpha_deg=90.0,
                num_points=250,
            )
            projection = make_points_stereo_projection(
                points=circle
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )
        # Draw zenith small circles
        for zenith in zeniths:
            circle = generate_small_circle(
                spheric_normal_deg=np.array([0.0, 0.0]),
                alpha_deg=zenith,
                num_points=250,
            )
            projection = make_points_stereo_projection(
                points=circle
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
        self._groups['Grids'] = self._groups.get('Grids', []) + [(grid, 'Azimuthal grid')]

    def _add_equatorial_grid(self):
        """
        Add equatorial grid to skychart
        """

        declinations = np.arange(-90.0, 90.0, self.config.grid_theta_step, dtype=np.float64)
        right_ascensions = np.arange(0, 180.0, self.config.grid_phi_step, dtype=np.float64)

        array_grid = []
        # Draw great circles right ascension
        for ra in right_ascensions:
            eq_circle = generate_small_circle(
                spheric_normal_deg=np.array([90.0, ra + 90.0]),
                alpha_deg=90.0,
                num_points=250,
            )
            _, horizontal_coords = get_horizontal_coords(
                config=self.config.__dict__,
                data=eq_circle,
            )
            projection = make_points_stereo_projection(
                points=horizontal_coords
            )
            array_grid.append(
                np.column_stack(
                    [
                        projection['angle'].astype(np.float64),
                        projection['radius'].astype(np.float64),
                    ]
                )
            )
        # Draw small circles declination
        for dec in declinations:
            eq_circle = generate_small_circle(
                spheric_normal_deg=np.array([0.0, 0.0]),
                alpha_deg=(90.0 - dec),
                num_points=250,
            )
            _, horizontal_coords = get_horizontal_coords(
                config=self.config.__dict__,
                data=eq_circle,
            )
            projection = make_points_stereo_projection(
                points=horizontal_coords
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
        self._groups['Grids'] = self._groups.get('Grids', []) + [(grid, 'Equatorial grid')]

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
            self._ax.set_theta_offset(self.random_angle)
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
                tick.tick2line.set_markersize(2)
                tick.tick2line.set_markeredgewidth(1)
        else:
            self._ax.set_xticks([])

        # Remove border
        self._ax.spines['polar'].set_visible(False)

        # Add circle around skychart, draw border
        r_max = 2.0
        circle = Circle((0, 0), r_max,
                        transform=self._ax.transData._b,
                        fill=False,
                        edgecolor='black',
                        linewidth=1.5,
                        alpha=1.0,
                        zorder=10)  # поверх всего

        self._ax.add_patch(circle)

        self._ax.xaxis.grid(False)
        self._ax.set_yticks([])
        self._ax.set_ylim((0.0, r_max))

    def _create_grouped_legend(self):
        """
        Create legend split by groups
        """
        groups = {k: v for k, v in self._groups.items() if v}
        if not groups:
            return

        n_groups = len(groups)
        n_columns = n_groups
        n_rows = 1
        group_items = list(groups.items())
        legend_height = 0.25 / n_rows
        vertical_spacing = 0.05

        for i, (title, items) in enumerate(group_items):
            row = i // n_columns
            col = i % n_columns

            handles, labels = zip(*items)

            if n_columns == 1:
                bbox_x = 0.5
            else:
                bbox_x = 0.1 + col * (0.8 / (n_columns - 1))

            bbox_y = -0.05 - row * (legend_height + vertical_spacing)

            legend = self._ax.legend(
                handles, labels,
                title=title,
                loc='upper center',
                bbox_to_anchor=(bbox_x, bbox_y),
                ncol=1,
                frameon=True,
                fancybox=True,
                borderaxespad=0.3
            )

            legend.get_title().set_fontweight('bold')
            self._ax.add_artist(legend)
