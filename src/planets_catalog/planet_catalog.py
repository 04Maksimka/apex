"""Module with planets catalog."""
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from numpy.typing import NDArray
import numpy as np
from astropy.coordinates import get_body, get_sun
from astropy.time import Time
from astropy.coordinates import SkyCoord


class Planets(IntEnum):
    """Planets of the Solar system."""
    SUN = 0
    MERCURY = 1
    VENUS = 2
    MOON = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8


@dataclass
class PlanetCatalog(object):
    """Planets Catalog."""

    PLANET_DTYPE = np.dtype([
        ('v_mag', np.float64),
        ('ra', np.float64),
        ('dec', np.float64),
        ('x', np.float64),
        ('y', np.float64),
        ('z', np.float64),
        ('planet_id', np.int32)
    ])

    @staticmethod
    def get_planet_color(planet: Planets) -> str:
        """

        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets:
        :param planet: Planets: 

        """
        color_dict = {
            Planets.SUN: 'yellow',
            Planets.MERCURY: 'gray',
            Planets.VENUS: 'gold',
            Planets.MOON: 'lightgray',
            Planets.MARS: 'red',
            Planets.JUPITER: 'peru',
            Planets.SATURN: 'khaki',
            Planets.URANUS: 'cyan',
            Planets.NEPTUNE: 'blue',
        }
        return color_dict.get(planet, 'orange')

    def get_planets(self, time: datetime) -> NDArray:
        """

        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime:
        :param time: datetime: 

        """
        t = Time(time)

        planet_values = np.array([p.value for p in Planets], dtype=np.int64)

        mag_values = np.array([-26.7, -0.42, -4.6, -12.74, -1.6,
                               -2.94, 0.46, 5.32, 7.78], dtype=np.float64)

        coords_array = SkyCoord(
            [
                get_sun(t)
                if p.name.lower() == 'sun'
                else get_body(p.name.lower(), t)
                for p in Planets
            ]
        )
        ra_values = coords_array.ra.rad
        dec_values = coords_array.dec.rad

        xyz_values = coords_array.cartesian.xyz.value   # (3, n)
        distances = coords_array.distance.value         # (n,)

        unit_xyz = xyz_values / distances[np.newaxis, :]

        result = np.zeros(len(planet_values), dtype=self.PLANET_DTYPE)
        result['v_mag'] = mag_values
        result['ra'] = ra_values
        result['dec'] = dec_values
        result['x'] = unit_xyz[0, :]
        result['y'] = unit_xyz[1, :]
        result['z'] = unit_xyz[2, :]
        result['planet_id'] = planet_values

        return result
