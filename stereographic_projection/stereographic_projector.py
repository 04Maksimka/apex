"""Module implementing main stereographic projection."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from numpy.typing import NDArray
import numpy as np
from matplotlib import pyplot as plt
from helpers.geometry import (
    get_horizontal_coords, make_stars_projections, make_circle_projection, generate_small_circle,
)
from hip_catalog.hip_catalog import CatalogConstraints, Catalog


@dataclass
class StereoProjConfig(object):
    """Class of configuration of the StereoProjector."""

    add_ecliptic: bool
    add_equator: bool
    add_galactic_equator: bool
    local_time: datetime
    latitude: float
    longitude: float

    def __post_init__(self):
        self.latitude = np.deg2rad(self.latitude)
        self.longitude = np.deg2rad(self.longitude)


class StereoProjector(object):
    """Class of the stereographic projector."""

    catalog: Catalog       # Star catalog
    config: StereoProjConfig    # Stereo projector configuration
    _fig: plt.Figure            # Skychart figure
    _ax: plt.Axes               # Skychart axes

    def __init__(self, config: StereoProjConfig, catalog: Catalog):
        self.config = config
        self.catalog = catalog

    def generate(self, constraints: Optional[CatalogConstraints]=None) -> plt.Figure:
        """
        Generate a projection.

        :return: figure
        """

        # Get catalog
        _ = self.catalog.get_stars(constraints)

        # From equatorial to horizontal
        star_view_data = self._make_star_views()

        # Make projections
        points_data = make_stars_projections(star_view_data, self.catalog.constraints)

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

        self._ax.legend()

        return self._fig

    def _make_star_views(self) -> NDArray:
        """
        Returns horizontal coordinates.

        :return: star view parameters
        """
        STAR_VIEW_DTYPE = np.dtype([
            ('v_mag', np.float32),  # visual magnitude, m
            ('zenith', np.float32),
            ('azimuth', np.float32),
            ('hip_id', np.int32),  # hip identifier
        ])

        _, azimuths, zeniths = get_horizontal_coords(self.config.__dict__, data=self.catalog.data)

        number_of_stars = self.catalog.number_of_stars
        star_view_data = np.zeros(number_of_stars, dtype=STAR_VIEW_DTYPE)
        star_view_data['v_mag'] = self.catalog.data['v_mag']
        star_view_data['zenith'] = zeniths
        star_view_data['azimuth'] = azimuths
        star_view_data['hip_id'] = self.catalog.data['hip_id']

        return star_view_data

    def _add_ecliptic(self):
        """
        Add ecliptic on skychart
        """

        RA = 270.0
        DEC = 66.5607

        ecliptic_eci_coords = generate_small_circle(
            spheric_normal=np.array([DEC, RA]),
            alpha=90.0,
            num_points=1000
        )

        _, azimuths, zeniths = get_horizontal_coords(config=self.config.__dict__, data=ecliptic_eci_coords)
        projection_coords = make_circle_projection(azimuths=azimuths, zeniths=zeniths)
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
            spheric_normal=np.array([90.0, 0.0]),
            alpha=90.0,
            num_points=1000
        )

        _, azimuths, zeniths = get_horizontal_coords(config=self.config.__dict__, data=equator_eci_coords)
        projection_coords = make_circle_projection(azimuths=azimuths, zeniths=zeniths)
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
            spheric_normal=np.array([DEC, RA]),
            alpha=90.0,
            num_points=1000
        )

        _, azimuths, zeniths = get_horizontal_coords(config=self.config.__dict__, data=galactic_eci_coords)
        projection_coords = make_circle_projection(azimuths=azimuths, zeniths=zeniths)
        self._ax.plot(
            projection_coords['angle'],
            projection_coords['radius'],
            c='blue',
            linewidth=1,
            label='Galactic equator'
        )

    def _create_polar_scatter(self, projection_data: NDArray):
        """
        Create a scatter plot in polar coordinates.

        :param data: projection points to place on figure
        """

        # Set up the figure with polar projection
        self._fig = plt.figure(figsize=(15, 12))
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
            alpha=0.7,
            linewidth=0.5,
        )

        self._ax.set_title("Skychart", va='bottom', fontsize=14, pad=20)
        self._ax.set_xlabel("Angle (θ)", labelpad=15)
        self._ax.grid(True)
        # ax.set_xticks([])
        self._ax.set_yticks([])
        self._ax.set_ylim((0.0, 2.0))
