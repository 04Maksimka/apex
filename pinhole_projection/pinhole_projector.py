"""Module with pinhole projector."""
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Optional, List, Dict
import numpy as np
from numpy.typing import NDArray
from matplotlib import pyplot as plt

from constellations_metadata.constellations_data import get_available_constellations, get_constellation_center
from helpers.geometry.geometry import make_pinhole_projection, mag_to_radius, generate_small_circle, \
    make_equatorial_grid_pinhole
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from pinhole_projection.constellation_renderer import ConstellationRenderer, draw_multiple_constellations
from planets_catalog.planet_catalog import PlanetCatalog, Planets


@dataclass
class ShotConditions:
    """ Shooting conditions. """
    center_direction: NDArray   # direction in ECI (unit vector)
    tilt_angle: float           # angle in degrees on which we rotate a camera

    def __post_init__(self):
        # Normalize direction vector
        self.center_direction /= np.linalg.norm(self.center_direction)


@dataclass
class CameraConfig:
    """ Physical camera configurations."""
    width: int          # frame width in pixels
    height: int         # frame height in pixels
    focal_length: float # camera focal length in pixels

    @classmethod
    def from_fov_and_aspect(
            cls,
            fov_deg: float,
            aspect_ratio: float,
            height_pix: int,
    ):
        """
        Create CameraConfig from field of view and aspect ratio.

        :param fov_deg: Horizontal field of view in degrees
        :param aspect_ratio: width/height ratio
        :param height_pix: height in pixels
        """

        # Calculate frame width
        width_pix = int(height_pix * aspect_ratio)

        # Calculate focal length from FOV and diagonal
        fov_rad = np.deg2rad(fov_deg)
        diagonal = np.sqrt(width_pix**2 + height_pix**2)
        focal_length_pix = (diagonal / 2) / np.tan(fov_rad / 2)

        return cls(width=width_pix, height=height_pix, focal_length=focal_length_pix)

@dataclass
class PinholeConfig:
    """Class of the pinhole projector configurations. """

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
    add_equatorial_grid: bool = False
    use_dark_mode: bool = False
    add_constellations: bool = False
    add_constellations_names: bool = False


@dataclass
class ProjectionResult:
    """Result of pinhole projection."""
    stars: NDArray      # Structured array with star projections
    planets: NDArray    # Structured array with planet projections


@dataclass
class ConstellationConfig(object):
    constellations_list: Optional[
        List[str]] = None  # If None, render all available
    constellation_color: str = 'gray'
    constellation_linewidth: float = 0.8
    constellation_alpha: float = 0.7
    constellation_color_map: Optional[Dict[str, str]] = None


class Pinhole(object):
    """Pinhole camera projector."""

    def __init__(
            self,
            shot_cond: ShotConditions,
            camera_cfg: CameraConfig,
            config: PinholeConfig,
            catalog: Catalog,
            planet_catalog: PlanetCatalog,
            constellation_config: Optional[ConstellationConfig] = None,
            constellations_renderer: Optional[ConstellationRenderer] = ConstellationRenderer(),
    ):
        """
        Initialize pinhole projector.

        :param shot_cond: Shot conditions
        :param camera_cfg: Camera configuration
        :param config: Configuration
        :param catalog: Star catalog instance
        :param planet_catalog: Planet catalog instance
        """

        self.shot_cond = shot_cond
        self.camera_config = camera_cfg
        self.constellation_config = constellation_config
        self.constellations_renderer = constellations_renderer
        self.config = config
        self.catalog = catalog
        self.planets_catalog = planet_catalog
        self._groups = {}
        self._star_projections = None
        self._planets_projections = None

    def _make_pinhole_views(self, data: NDArray, object_type: str = 'star') -> NDArray:
        """
        Returns coordinates in picture plane (pinhole projection).

        :param data: objects equatorial coordinates
        :param object_type: star or planet
        :return: view parameters
        """
        VIEW_DTYPE = np.dtype([
            ('v_mag', np.float32),
            ('x_pix', np.float32),
            ('y_pix', np.float32),
            ('size', np.float32),
            ('ra', np.float32),
            ('dec', np.float32),
            ('id', np.int32),
        ])

        valid_mask, picture_coords = make_pinhole_projection(
            center_direction=self.shot_cond.center_direction,
            tilt_dec=self.shot_cond.tilt_angle,
            image_width=self.camera_config.width,
            image_height=self.camera_config.height,
            focal_length=self.camera_config.focal_length,
            data=data
        )

        view_data = np.zeros(np.sum(valid_mask), dtype=VIEW_DTYPE)
        view_data['v_mag'] = data['v_mag'][valid_mask]
        view_data['x_pix'] = picture_coords['x_pix'][valid_mask]
        view_data['y_pix'] = picture_coords['y_pix'][valid_mask]
        view_data['ra'] = data['ra'][valid_mask]
        view_data['dec'] = data['dec'][valid_mask]
        view_data['size'] = mag_to_radius(
            magnitude=view_data['v_mag'],
            max_magnitude=self.catalog.constraints.max_magnitude,
            min_magnitude=self.catalog.constraints.min_magnitude
        )

        if object_type == 'star':
            view_data['id'] = data['hip_id'][valid_mask]
        elif object_type == 'planet':
            view_data['id'] = data['planet_id'][valid_mask]

        return view_data

    def generate(self, constraints: Optional[CatalogConstraints]=None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Generate a pinhole projection image.

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

        # Add equatorial grid
        if self.config.add_equatorial_grid:
            self._add_equatorial_grid()

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

        # Get stars data
        stars_data = self.catalog.get_stars(constraints)
        # From ECI to picture plane, make projection
        star_view_data = self._make_pinhole_views(
            data=stars_data,
            object_type='star'
        )
        self._star_projections = star_view_data
        # Create picture plane to place stars and other objects
        self._create_picture_plane()

        # Add planets
        if self.config.add_planets:
            planet_data = self.planets_catalog.get_planets(self.config.local_time)
            planet_view_data = self._make_pinhole_views(
                data=planet_data,
                object_type='planet'
            )
            self._planets_projections = planet_view_data
            self._add_planets()

    @property
    def projection_result(self) -> ProjectionResult:
        return ProjectionResult(stars=self._star_projections, planets=self._planets_projections)

    def _create_picture_plane(self):
        """
        Creates the figure and axes.
        """

        self._fig = plt.figure()
        self._ax = self._fig.add_subplot(111)

        # Create visualizations
        color = 'black'
        if self.config.use_dark_mode:
            color = 'white'
            plt.style.use('dark_background')

        self._ax.scatter(
            self._star_projections['x_pix'],
            self._star_projections['y_pix'],
            s=self._star_projections['size'],
            c=color
        )

        self._ax.set_ylim(bottom=0, top=self.camera_config.height)
        self._ax.set_xlim(left=0, right=self.camera_config.width)

        if not self.config.add_ticks:
            self._ax.set_xticks([])
            self._ax.set_yticks([])

    def _add_planets(self):
        """
        Add planets to image.
        """

        for planet_data in self._planets_projections:
            if planet_data['v_mag'] < self.catalog.constraints.max_magnitude:
                planet = Planets(planet_data['id'])
                name = planet.name.capitalize()
                color = self.planets_catalog.get_planet_color(planet)
                scatter = self._ax.scatter(
                    planet_data['x_pix'],
                    planet_data['y_pix'],
                    c=color,
                    s=max(planet_data['size'] * 3, 0.5),  # make planets larger for visibility
                    alpha=0.8,
                    linewidth=0.5,
                )
                # Add to the legend groups
                self._groups['Planets'] = self._groups.get('Planets', []) + [(scatter, name)]

    def _add_ecliptic(self):
        """
        Add ecliptic on image
        """

        RA = 270.0
        DEC = 66.5607

        ecliptic_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([90.0 - DEC, RA]),
            alpha_deg=90.0,
            num_points=1000
        )
        valid_mask, picture_coords = make_pinhole_projection(
            center_direction=self.shot_cond.center_direction,
            tilt_dec=self.shot_cond.tilt_angle,
            image_width=self.camera_config.width,
            image_height=self.camera_config.height,
            focal_length=self.camera_config.focal_length,
            data=ecliptic_eci_coords
        )
        line, = self._ax.plot(
            picture_coords['x_pix'][valid_mask],
            picture_coords['y_pix'][valid_mask],
            c='green',
            linewidth=1,
        )
        # Add to the legend groups if at leat one point on image
        if np.sum(valid_mask) > 0:
            self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Ecliptic')]

    def _add_equator(self):
        """
        Add equator on image
        """

        equator_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([0.0, 0.0]),
            alpha_deg=90.0,
            num_points=1000
        )
        valid_mask, picture_coords = make_pinhole_projection(
            center_direction=self.shot_cond.center_direction,
            tilt_dec=self.shot_cond.tilt_angle,
            image_width=self.camera_config.width,
            image_height=self.camera_config.height,
            focal_length=self.camera_config.focal_length,
            data=equator_eci_coords
        )
        line, = self._ax.plot(
            picture_coords['x_pix'][valid_mask],
            picture_coords['y_pix'][valid_mask],
            c='red',
            linewidth=1,
        )
        # Add to the legend groups if at leat one point on image
        if np.sum(valid_mask) > 0:
            self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Celestial equator')]

    def _add_galactic_equator(self):
        """
        Add galactic equator on image
        """

        # Galactical center
        RA = 192.85948
        DEC = 27.12825

        galactic_eci_coords = generate_small_circle(
            spheric_normal_deg=np.array([90.0 - DEC, RA]),
            alpha_deg=90.0,
            num_points=1000
        )
        valid_mask, picture_coords = make_pinhole_projection(
            center_direction=self.shot_cond.center_direction,
            tilt_dec=self.shot_cond.tilt_angle,
            image_width=self.camera_config.width,
            image_height=self.camera_config.height,
            focal_length=self.camera_config.focal_length,
            data=galactic_eci_coords
        )
        line, = self._ax.plot(
            picture_coords['x_pix'][valid_mask],
            picture_coords['y_pix'][valid_mask],
            c='blue',
            linewidth=1,
        )
        # Add to the legend groups if at leat one point on image
        if np.sum(valid_mask) > 0:
            self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Galactic equator')]

    def _add_equatorial_grid(self):
        """
        Add equatorial grid on image
        """

        grid = make_equatorial_grid_pinhole(
            center_direction=self.shot_cond.center_direction,
            tilt_dec=self.shot_cond.tilt_angle,
            image_width=self.camera_config.width,
            image_height=self.camera_config.height,
            focal_length=self.camera_config.focal_length,
            grid_step_ra=self.config.grid_phi_step,
            grid_step_dec=self.config.grid_theta_step,
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
            stars=self._star_projections
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
                                                 [(first_lc, f'Constellation segments ({len(lcs)})')]

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

            if np.dot(get_constellation_center(constellation), self.shot_cond.center_direction) > 0:
                _, center_projection = make_pinhole_projection(
                    center_direction=self.shot_cond.center_direction,
                    tilt_dec=self.shot_cond.tilt_angle,
                    image_width=self.camera_config.width,
                    image_height=self.camera_config.height,
                    focal_length=self.camera_config.focal_length,
                    data=eci_center,
                )
                self._ax.annotate(
                    text=constellation,
                    xy=(center_projection['x_pix'][0], center_projection['y_pix'][0]),
                    xytext=(0, 0),
                    fontsize=10,
                    textcoords='offset points',
                    color='gray',
                    ha = 'center',
                    va = 'center',
                )

    def _create_grouped_legend(self):
        """
        Create legend below the plot for landscape orientation
        """
        groups = {k: v for k, v in self._groups.items() if v}
        if not groups:
            return

        # Sort groups by number of items (largest first)
        groups = dict(sorted(groups.items(), key=lambda x: len(x[1]), reverse=True))

        n_groups = len(groups)
        group_items = list(groups.items())

        # For landscape, we can fit more groups in a row
        # Calculate optimal number of columns
        n_columns = n_groups
        n_rows = 1

        # Calculate positions for each legend
        # We'll place legends in a grid below the plot
        total_height = 0.15 * n_rows  # Adjust based on number of rows
        vertical_spacing = 0.02

        # Adjust axis position to make room for legend below
        ax_pos = self._ax.get_position()

        # For landscape, we reduce height and shift up
        new_height = ax_pos.height # Reduce height by 15%
        new_y0 = ax_pos.y0 + (ax_pos.height - new_height)
        self._ax.set_position([ax_pos.x0, new_y0, ax_pos.width, new_height])

        # Create legends in a grid
        for i, (title, items) in enumerate(group_items):
            row = i // n_columns
            col = i % n_columns

            handles, labels = zip(*items)

            # Calculate position in figure coordinates
            # Distribute evenly horizontally
            col_width = 0.8 / n_columns  # Use 90% of width
            x_pos = 0.075 + col * col_width + col_width / 2  # Center of column

            # Position below the plot
            y_pos = 0.15 + (n_rows - row - 1) * 0.08  # Start from bottom

            # Create legend
            legend = self._ax.legend(
                handles, labels,
                title=title,
                loc='upper center',
                bbox_to_anchor=(x_pos, y_pos),
                bbox_transform=self._fig.transFigure,  # Use figure coordinates
                ncol=1,
                frameon=True,
                fancybox=True,
                borderaxespad=0.3,
                fontsize=8,
                handlelength=1.5
            )

            # Make title bold
            legend.get_title().set_fontweight('bold')
            legend.get_title().set_fontsize(10)

            # Add legend to figure (outside axis)
            self._ax.add_artist(legend)
