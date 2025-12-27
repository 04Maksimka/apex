"""Module with planets catalog."""
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from numpy.typing import NDArray
import numpy as np
import astropy.units as u
from astropy.coordinates import get_body, get_sun
from astropy.time import Time
from hip_catalog.hip_catalog import Catalog


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

    @staticmethod
    def get_planet_color(planet: Planets) -> str:
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

    @staticmethod
    def get_planets(time: datetime) -> NDArray:
        t = Time(time)
        mag_dict = {
            Planets.SUN: -26.7,
            Planets.MERCURY: -0.42,
            Planets.VENUS: -4.6,
            Planets.MOON: -12.74,
            Planets.MARS: -1.6,
            Planets.JUPITER: -2.94,
            Planets.SATURN: 0.46,
            Planets.URANUS: 5.32,
            Planets.NEPTUNE: 7.78,
        }
        names = ['sun', 'mercury', 'venus', 'moon', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
        data_list = []
        for p in Planets:
            name = names[p.value]
            if name == 'sun':
                coord = get_sun(t)
            elif name == 'moon':
                coord =  get_body('moon', t)
            else:
                coord = get_body(name, t)
            ra = coord.ra.to_value(u.rad)
            dec = coord.dec.to_value(u.rad)
            unit_xyz = coord.cartesian.xyz.value / coord.distance.value
            x, y, z = unit_xyz
            v_mag = mag_dict[p]
            hip_id = -p.value - 1
            data_list.append((v_mag, ra, dec, x, y, z, hip_id))

        return np.array(data_list, dtype=Catalog.STAR_DTYPE)
