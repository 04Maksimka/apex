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
from planets_catalog.planet_catalog import PlanetCatalog, Planets


@dataclass
class StereoProjConfig(object):
    """Class of configuration of the StereoProjector."""

    add_ecliptic: bool
    add_equator: bool
    add_galactic_equator: bool
    add_planets: bool
    local_time: datetime
    latitude: float
    longitude: float

    def __post_init__(self):
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
        star_view_data = self._make_horizontal_views(self.catalog.data)

        # Make projections
        points_data = make_stars_projections(star_view_data, self.catalog.constraints)

        # Make figure with projections
        self._create_polar_scatter(points_data)

        # Add planets
        if self.config.add_planets:
            planet_data = self.planets_catalog.get_planets(self.config.local_time)
            planet_view_data = self._make_horizontal_views(planet_data)
            planet_points_data = make_stars_projections(planet_view_data, self.catalog.constraints)
            self._add_planets(planet_points_data)

        # Add ecliptic
        if self.config.add_ecliptic:
            self._add_ecliptic()

        # Add equator
        if self.config.add_equator:
            self._add_equator()

        # Add galactic equator
        if self.config.add_galactic_equator:
            self._add_galactic_equator()

        box = self._ax.get_position()
        self._ax.set_position((box.x0, box.y0, box.width * 0.8, box.height))

        # Put a legend to the bottom of the current axis
        self._ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=5)

        return self._fig

    def _make_horizontal_views(self, data: NDArray) -> NDArray:
        """
        Returns horizontal coordinates.

        :return: view parameters
        """
        STAR_VIEW_DTYPE = np.dtype([
            ('v_mag', np.float32),  # visual magnitude, m
            ('zenith', np.float32),
            ('azimuth', np.float32),
            ('hip_id', np.int32),  # hip identifier
        ])

        _, azimuths, zeniths = get_horizontal_coords(self.config.__dict__, data=data)

        number_of_stars = data.shape[0]
        star_view_data = np.zeros(number_of_stars, dtype=STAR_VIEW_DTYPE)
        star_view_data['v_mag'] = data['v_mag']
        star_view_data['zenith'] = zeniths
        star_view_data['azimuth'] = azimuths
        star_view_data['hip_id'] = data['hip_id']

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
        Create a scatter plot in polar coordinates for stars.

        :param projection_data: projection points to place on figure
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
            alpha=1,
            linewidth=0.5,
        )

        # self._ax.set_title("Skychart", va='bottom', fontsize=14, pad=20)
        # self._ax.grid(True)
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        self._ax.set_ylim((0.0, 2.0))

    def _add_planets(self, projection_data: NDArray):
        """
        Add planets to the scatter plot.

        :param projection_data: projection points for planets
        """
        for p in projection_data:
            if p['hip_id'] >= 0:
                continue  # not a planet
            planet_id = -p['hip_id'] - 1
            planet = Planets(planet_id)
            name = planet.name.capitalize()
            color = self.planets_catalog.get_planet_color(planet)
            self._ax.scatter(
                p['angle'],
                p['radius'],
                c=color,
                s=p['size'] * 3,  # make planets larger for visibility
                alpha=0.8,
                linewidth=0.5,
                label=name,
            )
