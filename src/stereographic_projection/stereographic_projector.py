"""Module implementing main stereographic projection."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from numpy.typing import NDArray
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

from src.constellations_metadata.constellations_data import get_available_constellations, get_constellation_center
from src.helpers.geometry.geometry import (
    get_horizontal_coords, make_stereo_projection, make_points_stereo_projection, generate_small_circle, mag_to_radius,
)
from src.hip_catalog.hip_catalog import CatalogConstraints, Catalog
from src.planets_catalog.planet_catalog import PlanetCatalog, Planets
from matplotlib.collections import LineCollection

from src.stereographic_projection.constellation_renderer_stereo import ConstellationRendererStereo, \
    draw_multiple_constellations


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
    add_constellations: bool = False
    add_constellations_names: bool = False
    add_zenith: bool = False
    add_poles: bool = False
    random_origin: bool = False

    def __post_init__(self):
        # Store in radians
        self.latitude = np.deg2rad(self.latitude)
        self.longitude = np.deg2rad(self.longitude)


@dataclass
class ConstellationConfig(object):
    constellations_list: Optional[
        List[str]] = None  # If None, render all available
    constellation_color: str = 'gray'
    constellation_linewidth: float = 0.8
    constellation_alpha: float = 0.7
    constellation_color_map: Optional[Dict[str, str]] = None


@dataclass
class ProjectionResult:
    """Result of pinhole projection."""
    stars: NDArray      # Structured array with star projections
    planets: NDArray    # Structured array with planet projections


class StereoProjector(object):
    """Class of the stereographic projector."""

    def __init__(
        self,
        config: StereoProjConfig,
        catalog: Catalog,
        planets_catalog: PlanetCatalog,
        constellations_renderer: Optional[ConstellationRendererStereo] = ConstellationRendererStereo(),
        constellation_config: Optional[ConstellationConfig] = None,
        random_angle: float = np.random.uniform(0.0, 2*np.pi)
    ):
        self.config = config
        self.constellation_config = constellation_config
        self.constellations_renderer = constellations_renderer
        self.catalog = catalog
        self.planets_catalog = planets_catalog
        self.random_angle = random_angle
        self._groups = {}  # Legend groups - initialize as instance variable
        self._star_projections = None
        self._planets_projections = None

    def generate(self, constraints: Optional[CatalogConstraints]=None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Generate a stereographic projection image.

        :param constraints: Catalog constraints
        :return: figure
        """

        # Make objects projections
        self.project(constraints=constraints)

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

        # Add zenith
        if self.config.add_zenith:
            self._add_zenith()

        # Add celestial poles (one visible pole)
        if self.config.add_poles:
            self._add_poles()

        # Add constellation lines
        if self.config.add_constellations:
            self._add_constellations()

        # Add constellation names
        if self.config.add_constellations_names:
            self._add_constellations_names()

        # Put a legend to the bottom of the current axis
        self._create_grouped_legend()

        return self._fig, self._ax

    def project(self, constraints: CatalogConstraints):
        """
        Objects projection maker

        :param constraints: Catalog constraints
        :return:
        """
        # Get catalog
        stars_data = self.catalog.get_stars(constraints)

        # From equatorial to horizontal
        star_hor_view_data = self._make_horizontal_views(
            data=stars_data,
            object_type='star'
        )
        # Make projections
        star_view_data = self._make_stereo_views(
            data=star_hor_view_data,
        )
        self._star_projections = star_view_data

        # Make figure with projections
        self._create_polar_scatter(self._star_projections)

        # Add planets
        if self.config.add_planets:
            planet_data = self.planets_catalog.get_planets(self.config.local_time)
            planet_hor_view_data = self._make_horizontal_views(
                data=planet_data,
                object_type='planet'
            )
            planet_view_data = self._make_stereo_views(
                data=planet_hor_view_data,
            )
            self._add_planets(planet_view_data)
            self._planets_projections = planet_view_data

    def _make_stereo_views(self, data: NDArray) -> NDArray:
        """
        Returns a stereographic projection views to plot

        :param data: horizontal coordinates data
        :return: projection data to plot
        """

        VIEW_DTYPE = np.dtype([
            ('size', np.float32),
            ('v_mag', np.float32),
            ('radius', np.float32),
            ('angle', np.float32),
            ('id', np.int32),
        ])
        projection_data = make_stereo_projection(
            view_data=data
        )

        view_data = np.zeros(len(data), dtype=VIEW_DTYPE)
        view_data['radius'] = projection_data['radius']
        view_data['angle'] = projection_data['angle']
        view_data['v_mag'] = projection_data['v_mag']
        view_data['size'] = mag_to_radius(
            magnitude=projection_data['v_mag'],
            max_magnitude=self.catalog.constraints.max_magnitude,
            min_magnitude=self.catalog.constraints.min_magnitude
        )
        view_data['id'] = projection_data['id']

        return view_data

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

        valid_mask, horizontal_coords = get_horizontal_coords(
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
            data=data
        )

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
        """
        Adds zenith projection point on skychart.
        """

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
        """
        Adds pole projection point on skychart.
        """

        POINT_DTYPE = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        north_pole = np.array([(0, 0, 1)], dtype=POINT_DTYPE)
        south_pole = np.array([(0, 0, -1)], dtype=POINT_DTYPE)

        _, north_horizontal = get_horizontal_coords(
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
            data=north_pole
        )
        if north_horizontal['zenith'] < np.pi / 2:
            north_projection = make_points_stereo_projection(
                points=north_horizontal
            )
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
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
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
        Add ecliptic on skychart.
        """

        RA = 270.0
        DEC = 66.5607

        ecliptic_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([90.0 - DEC, RA]),
            alpha_deg=90.0,
            num_points=1000
        )
        _, horizontal_coords = get_horizontal_coords(
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
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
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
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
            longitude=self.config.longitude,
            latitude=self.config.latitude,
            local_time=self.config.local_time,
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
            if planet_data['v_mag'] < self.catalog.constraints.max_magnitude:
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
                longitude=self.config.longitude,
                latitude=self.config.latitude,
                local_time=self.config.local_time,
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
            _, horizontal_coords =get_horizontal_coords(
                longitude=self.config.longitude,
                latitude=self.config.latitude,
                local_time=self.config.local_time,
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

        grid = LineCollection(
            array_grid,
            label='Equatorial grid',
            colors='magenta',
            alpha=0.25,
            linewidth=0.5
        )
        self._ax.add_collection(grid)
        self._groups['Grids'] = self._groups.get('Grids', []) + [(grid, 'Equatorial grid')]

    def _add_constellations(self):
        """Adds constellation line patterns to the projection."""

        if self.constellation_config.constellations_list is not None:
            separate = True
            constellations_to_render = self.constellation_config.constellations_list
        else:
            separate = False
            constellations_to_render = get_available_constellations()

        # Get constellation segments
        constellation_segments = self.constellations_renderer.get_multiple_constellation_segments(
            constellations=constellations_to_render,
            projection_data=self._star_projections
        )

        if not constellation_segments:
            return

        # Draw constellations
        lcs = draw_multiple_constellations(
            ax=self._ax,
            constellation_segments=constellation_segments,
            color=self.constellation_config.constellation_color,
            linewidth=self.constellation_config.constellation_linewidth,
            alpha=self.constellation_config.constellation_alpha,
            color_map=self.constellation_config.constellation_color_map,
            use_collection=True
        )

        # Add to legend groups
        if lcs:
            if separate:
                for name, params in lcs.items():
                    self._groups['Constellations'] = self._groups.get('Constellations', []) +\
                                                     [(params['lc'], f"{params['name']}")]
            else:
                # Get first line collection for legend
                first_lc = list(lcs.values())[0]['lc']
                self._groups['Constellations'] = self._groups.get('Constellations', []) + \
                                                 [(first_lc, f'Constellations ({len(lcs)})')]

    def _add_constellations_names(self):
        """
        Adds constellation names on skychart.
        """

        POINT_DTYPE = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4')])

        if self.constellation_config.constellations_list is not None:
            constellations_to_render = self.constellation_config.constellations_list
        else:
            constellations_to_render = get_available_constellations()

        for constellation in constellations_to_render:
            eci_center = np.array(
                [tuple(get_constellation_center(constellation))],
                dtype=POINT_DTYPE
            )
            _, center_horizontal = get_horizontal_coords(
                longitude=self.config.longitude,
                latitude=self.config.latitude,
                local_time=self.config.local_time,
                data=eci_center
            )

            # If we can observe constellation
            if center_horizontal['zenith'] < np.pi / 2:
                center_projection = make_points_stereo_projection(
                    points=center_horizontal
                )
                self._ax.annotate(
                    text=constellation,
                    xy=(center_projection['angle'][0], center_projection['radius'][0]),
                    xytext=(0, 0),
                    fontsize=7,
                    textcoords='offset points',
                    color='gray',
                    ha = 'center',
                    va = 'center',
                )

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
        """Create a grouped legend for the visualization."""
        groups = {k: v for k, v in self._groups.items() if v}
        if not groups:
            return

        # Sort groups by size
        groups = dict(sorted(groups.items(), key=lambda x: len(x[1]), reverse=True))

        # Determine layout
        n_groups = len(groups)

        # Calculate number of columns based on number of groups
        if n_groups <= 2:
            n_columns = n_groups
        elif n_groups <= 4:
            n_columns = 2
        else:
            n_columns = min(3, n_groups)

        group_items = list(groups.items())

        # Calculate positions with proper spacing
        column_width = 0.96 / n_columns
        vertical_spacing = 0.12  # Increased spacing between rows

        for i, (title, items) in enumerate(group_items):
            if not items:
                continue

            handles, labels = zip(*items)

            # Calculate column and row
            col = i % n_columns
            row = i // n_columns

            # Position legends with proper spacing
            bbox_x = 0.02 + col * column_width
            bbox_y = -0.05 - (row * vertical_spacing)

            legend = self._ax.legend(
                handles, labels,
                title=title,
                loc='upper left',
                fontsize=8,
                bbox_to_anchor=(bbox_x, bbox_y),
                frameon=True,
                fancybox=True,
                borderaxespad=0.2,
                ncol=1  # Single column per legend group
            )

            legend.get_title().set_fontweight('bold')
            legend.get_title().set_fontsize(9)
            self._ax.add_artist(legend)

        # Adjust figure bottom margin to accommodate legends
        max_rows = (n_groups + n_columns - 1) // n_columns
        bottom_margin = 0.05 + (max_rows * vertical_spacing)
        self._fig.subplots_adjust(bottom=bottom_margin)
