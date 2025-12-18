"""Module with astronomical geometrical functions."""
from typing import Tuple, Union
from stereographic_projection.hip_catalog.hip_catalog import CatalogConstraints, NumpyCatalog
from stereographic_projection.helpers.time import vequinox_hour_angle
from numpy.typing import NDArray
import numpy as np


def get_horizontal_coords(config: dict, catalog: NumpyCatalog) -> Tuple[NDArray, NDArray, NDArray]:
    """
    Get horizontal coordinates from catalog data.

    :param config: place configuration
    :param catalog: star catalog data
    :return: horizontal coordinates, zenith distances and azimuths
    """

    # Get ECI star coordinates
    eci_coords = np.column_stack([catalog.data['x'], catalog.data['y'], catalog.data['z']]).T

    # Calculate local sidereal time
    sidereal_time = vequinox_hour_angle(
        longitude=config['longitude'],
        local=config['local_time']
    )

    # Rotate ECI (XYZ) to "cartesian" equatorial system (X'Y'Z'),
    # so Z' is directed to the North celestial pole, X' --- to the West point
    latitude = config['latitude']
    sl = np.sin(latitude)
    cl = np.cos(latitude)
    st = np.sin(sidereal_time)
    ct = np.cos(sidereal_time)
    rotation_matrix = np.array(
        [
            [st, -ct, 0],
            [sl * ct, sl * st, -cl],
            [cl * ct, cl * st, sl]
        ]
    )
    cartesian_hor_coords =  rotation_matrix @ eci_coords

    # 0, 1, 2 is x, y, z below
    azimuths = np.atan2(cartesian_hor_coords[0, :], cartesian_hor_coords[1, :]) - np.pi / 2
    zeniths = np.arccos(cartesian_hor_coords[2, :])

    return cartesian_hor_coords, azimuths, zeniths


def mag_to_radius(magnitude: Union[float, NDArray[np.float32]], constrains: CatalogConstraints) -> Union[float, NDArray[np.float32]]:
    """
    Returns radius of the point corresponds to given star magnitude.
    :param magnitude: star magnitude(s)
    :param constrains: constrains criteria
    :return: radius: star image radius
    """
    mag_criteria = constrains.max_magnitude
    diff = mag_criteria - magnitude
    radii = 1.5 * np.maximum(diff, 0.0)
    return radii


def make_point_projections(star_view_data: NDArray, constraints: CatalogConstraints) -> NDArray:
    """
    Returns star point projections array.

    :param star_view_data: observed stars parameters in horizontal coordinates
    :param constraints: catalog constraints
    :return: star image point parameters
    """
    PROJECTION_DTYPE = np.dtype([
        ('size', np.float32),
        ('radius', np.float32),
        ('angle', np.float32),
        ('hip_id', np.int32),
    ])
    number_of_stars = star_view_data.shape[0]

    points_data = np.zeros(number_of_stars, dtype=PROJECTION_DTYPE)
    points_data['size'] = mag_to_radius(star_view_data['v_mag'], constraints)
    points_data['radius'] = 2 * np.tan(star_view_data['zenith'] / 2.0)
    points_data['angle'] = star_view_data['azimuth']
    points_data['hip_id'] = star_view_data['hip_id']

    return points_data