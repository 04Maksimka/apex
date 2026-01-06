"""Module with pinhole projector."""
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Optional
import numpy as np
from matplotlib.collections import LineCollection
from numpy.typing import NDArray
from matplotlib import pyplot as plt

from helpers.geometry.geometry import make_pinhole_projection, mag_to_radius, generate_small_circle, \
    make_equatorial_grid_pinhole
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
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
    add_horizontal_grid: bool = False
    add_equatorial_grid: bool = False
    use_dark_mode: bool = False


@dataclass
class ProjectionResult:
    """Result of pinhole projection."""
    stars: NDArray      # Structured array with star projections
    planets: NDArray    # Structured array with planet projections


class Pinhole(object):
    """Pinhole camera projector."""

    def __init__(
            self,
            shot_cond: ShotConditions,
            camera_cfg: CameraConfig,
            config: PinholeConfig,
            catalog: Catalog,
            planet_catalog: PlanetCatalog
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

        # Add horizontal grid
        if self.config.add_horizontal_grid:
            self._add_horizontal_grid()

        # Add equatorial grid
        if self.config.add_equatorial_grid:
            self._add_equatorial_grid()

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
        Add ecliptic on skychart
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
        # Add to the legend groups
        self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Ecliptic')]

    def _add_equator(self):
        """
        Add equator on skychart
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
        # Add to the legend groups
        self._groups['Great circles'] = self._groups.get('Great circles', []) + [(line, 'Galactic equator')]

    def _add_equatorial_grid(self):
        """
        Add equatorial grid to skychart
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

    def _add_horizontal_grid(self):
        pass

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


