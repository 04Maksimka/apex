"""Module implementing main stereographic projection."""
from dataclasses import dataclass
from datetime import datetime
from numpy.typing import NDArray
import numpy as np
from matplotlib import pyplot as plt
from stereographic_projection.hip_catalog.hip_catalog import NumpyCatalog
from stereographic_projection.helpers.geometry import get_horizontal_coords, make_point_projections


@dataclass
class StereoProjConfig(object):
    """Class of configuration of the StereoProjector."""

    add_ecliptic: bool
    local_time: datetime
    latitude: float
    longitude: float

    def __post_init__(self):
        self.latitude = np.deg2rad(self.latitude)
        self.longitude = np.deg2rad(self.longitude)



class StereoProjector(object):
    """Class of the stereographic projector."""

    def __init__(self, config: StereoProjConfig, catalog: NumpyCatalog):
        self.config = config
        self.catalog = catalog

    def generate(self) -> plt.Figure:
        """
        Generate a projection.

        :return: figure
        """

        # Get catalog
        catalog_data = self.catalog.get_stars()
        # From equatorial to horizontal
        star_view_data = self._make_star_views()
        # Make projections
        points_data = make_point_projections(star_view_data, self.catalog.constraints)
        # Make figure with projections
        fig, _ = self._create_polar_scatter(points_data)

        return fig


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

        _, azimuths, zeniths = get_horizontal_coords(self.config.__dict__, catalog=self.catalog)

        number_of_stars = self.catalog.number_of_stars
        star_view_data = np.zeros(number_of_stars, dtype=STAR_VIEW_DTYPE)
        star_view_data['v_mag'] = self.catalog.data['v_mag']
        star_view_data['zenith'] = zeniths
        star_view_data['azimuth'] = azimuths
        star_view_data['hip_id'] = self.catalog.data['hip_id']

        return star_view_data



    @staticmethod
    def _create_polar_scatter(data: NDArray):
        """
        Create a scatter plot in polar coordinates.

        :param data: projection points to place on figure
        """

        # Set up the figure with polar projection
        fig = plt.figure(figsize=(15, 12))
        ax = fig.add_subplot(111, projection='polar')

        # Get parameters from projections data array
        sizes = data['size']
        angles = data['angle']
        radii = data['radius']

        # Make scatter
        ax.scatter(
            angles,
            radii,
            c='black',
            s=sizes,
            alpha=0.7,
            edgecolors='white',
            linewidth=0.5,
        )

        ax.set_title("Skychart", va='bottom', fontsize=14, pad=20)
        ax.set_xlabel("Angle (θ)", labelpad=15)
        ax.grid(True)
        # ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim((0.0, 2.0))

        return fig, ax
