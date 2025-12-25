"""Module with astronomical geometrical functions."""
from typing import Tuple, Union
from helpers.time.time import vequinox_hour_angle
from numpy.typing import NDArray
import numpy as np
from hip_catalog.hip_catalog import CatalogConstraints


def get_horizontal_coords(config: dict, data: NDArray) -> Tuple[NDArray, NDArray, NDArray]:
    """
    Get horizontal coordinates from catalog data.

    :param config: place configuration
    :param data: data to make conversion into horizontal coordinates
    :return: horizontal coordinates, zenith distances and azimuths
    """

    # Get ECI star coordinates
    eci_coords = np.column_stack([data['x'], data['y'], data['z']]).T

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


def mag_to_radius(
        magnitude: Union[float, NDArray[np.float32]],
        constrains: CatalogConstraints,
) -> Union[float, NDArray[np.float32]]:
    """
    Returns radius of the point corresponds to given star magnitude.
    :param magnitude: star magnitude(s)
    :param constrains: constrains criteria
    :return: radius: star image radius
    """
    mag_criteria = constrains.max_magnitude
    diff = mag_criteria - magnitude
    radii = np.maximum(diff, 0.0)
    return radii


def make_stars_projections(star_view_data: NDArray, constraints: CatalogConstraints) -> NDArray:
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

def generate_small_circle(spheric_normal: NDArray, alpha: float, num_points: int) -> NDArray:
    """
    Generate a small circle on unit sphere in ECI coordinates.

    :param spheric_normal: spherical coordinates on the normal to hte place of circle, angles in degrees
    :param alpha: angle between any radis vector of the point on small circle and normal
    :param num_points: number of points to generate
    :return: array of points in cartesian ECI coordinates
    """

    POINTS_DTYPE = np.dtype([
        ('x', np.float32),
        ('y', np.float32),
        ('z', np.float32),
    ])

    theta = np.deg2rad(spheric_normal[0])
    phi = np.deg2rad(spheric_normal[1])
    n = np.array(
        [
            np.cos(theta) * np.cos(phi),
            np.cos(theta) * np.sin(phi),
            np.sin(theta)
        ]
    )
    a = np.zeros_like(n)
    if not np.isclose(abs(n[2]), 1.0):
        a[2] = 1.0
    else:
        a[0] = 1.0

    u = np.cross(a, n)
    u = u / np.linalg.norm(u)

    v = np.cross(n, u)

    phi = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    alpha = np.deg2rad(alpha)
    cos_alpha = np.cos(alpha)
    sin_alpha = np.sin(alpha)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)

    points = np.zeros(num_points, dtype=POINTS_DTYPE)
    points['x'] = cos_alpha * n[0] + sin_alpha * (cos_phi * u[0] + sin_phi * v[0])
    points['y'] = cos_alpha * n[1] + sin_alpha * (cos_phi * u[1] + sin_phi * v[1])
    points['z'] = cos_alpha * n[2] + sin_alpha * (cos_phi * u[2] + sin_phi * v[2])

    return points

def make_circle_projection(azimuths: NDArray, zeniths: NDArray) -> NDArray:
    """
    Returns star point projections array.

    :param points: horizontal coordinates of circle points
    :return: projection point polar coordinates
    """
    PROJECTION_DTYPE = np.dtype([
        ('radius', np.float32),
        ('angle', np.float32),
    ])
    number_of_stars = azimuths.shape[0]

    points_data = np.zeros(number_of_stars, dtype=PROJECTION_DTYPE)
    points_data['radius'] = 2 * np.tan(zeniths / 2.0)
    points_data['angle'] = azimuths

    return points_data
