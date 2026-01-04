"""Module with astronomical geometrical functions."""
from typing import Tuple, Union

from helpers.time.time import vequinox_hour_angle
from numpy.typing import NDArray
import numpy as np
from hip_catalog.hip_catalog import CatalogConstraints


def get_horizontal_coords(config: dict, data: NDArray) -> NDArray:
    """
    Get horizontal coordinates from catalog data.

    :param config: place configuration
    :param data: data to make conversion into horizontal coordinates
    :return: horizontal coordinates, zenith distances and azimuths
    """
    HORIZONTAL_DTYPE = np.dtype([
        ('x', np.float32),
        ('y', np.float32),
        ('z', np.float32),
        ('azimuth', np.float32),
        ('zenith', np.float32),
    ])

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
    rotation_latitude = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, sl, -cl],
            [0.0, cl, sl]
        ]
    )
    rotation_time = np.array(
        [
            [st, -ct, 0.0],
            [ct, st, 0.0],
            [0.0, 0.0, 1.0]
        ]
    )
    rotation_matrix = rotation_latitude @ rotation_time
    cartesian_hor_coords =  rotation_matrix @ eci_coords

    # 0, 1, 2 is x, y, z below
    horizontal_coords = np.zeros(eci_coords.shape[1], dtype=HORIZONTAL_DTYPE)
    horizontal_coords['x'] = cartesian_hor_coords[0, :]
    horizontal_coords['y'] = cartesian_hor_coords[1, :]
    horizontal_coords['z'] = cartesian_hor_coords[2, :]
    horizontal_coords['azimuth'] = np.atan2(cartesian_hor_coords[0, :], cartesian_hor_coords[1, :])
    horizontal_coords['zenith'] = np.arccos(cartesian_hor_coords[2, :])

    return horizontal_coords


def mag_to_radius(
        magnitude: Union[float, NDArray[np.float32]],
        constraints: CatalogConstraints,
) -> Union[float, NDArray[np.float32]]:
    """
    Returns radius of the point corresponds to given star magnitude.
    :param magnitude: star magnitude(s)
    :param constraints: constrains criteria
    :return: radius: star image radius
    """
    mag_criteria = constraints.max_magnitude
    diff = mag_criteria - magnitude
    radii = np.maximum(diff, 0.0)
    return radii ** 1.3


def make_projections(view_data: NDArray, constraints: CatalogConstraints) -> NDArray:
    """
    Returns point projections array.

    :param view_data: observed object parameters in horizontal coordinates
    :param constraints: constraints
    :return: image point parameters
    """

    PROJECTION_DTYPE = np.dtype([
        ('size', np.float32),
        ('radius', np.float32),
        ('angle', np.float32),
        ('id', np.int32),
    ])

    points_data = np.zeros(view_data.shape[0], dtype=PROJECTION_DTYPE)
    points_data['size'] = mag_to_radius(view_data['v_mag'], constraints)
    points_data['radius'] = 2 * np.tan(view_data['zenith'] / 2.0)
    points_data['angle'] = view_data['azimuth']

    points_data['id'] = view_data['id']

    return points_data

def generate_small_circle(spheric_normal_deg: NDArray, alpha_deg: float, num_points: int) -> NDArray:
    """
    Generate a small circle on unit sphere in ECI coordinates.

    :param spheric_normal_deg: spherical coordinates on the normal to hte place of circle, angles in degrees
    :param alpha_deg: angle between any radis vector of the point on small circle and normal
    :param num_points: number of points to generate
    :return: array of points in cartesian ECI coordinates
    """

    POINTS_DTYPE = np.dtype([
        ('x', np.float32),
        ('y', np.float32),
        ('z', np.float32),
        ('theta', np.float32),
        ('phi', np.float32),
    ])

    # Extract angles, convert to radians
    theta = np.deg2rad(spheric_normal_deg[0])
    phi = np.deg2rad(spheric_normal_deg[1])

    # Define normal in cartesian coordinates
    normal = np.array(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta)
        ]
    )

    # Define ECI z-axis
    up_vec = np.array([0.0, 0.0, 1.0])
    # If normal is close to zenith axis choose y-axis
    if np.isclose(abs(normal[2]), 1.0):
        up_vec = np.array([0.0, 1.0, 0.0])

    u = np.cross(up_vec, normal)
    u = u / np.linalg.norm(u)

    v = np.cross(normal, u)

    phi = np.linspace(0, 2 * np.pi, num_points)
    alpha_rad = np.deg2rad(alpha_deg)
    cos_alpha = np.cos(alpha_rad)
    sin_alpha = np.sin(alpha_rad)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)

    points = np.zeros(num_points, dtype=POINTS_DTYPE)
    points['x'] = cos_alpha * normal[0] + sin_alpha * (cos_phi * u[0] + sin_phi * v[0])
    points['y'] = cos_alpha * normal[1] + sin_alpha * (cos_phi * u[1] + sin_phi * v[1])
    points['z'] = cos_alpha * normal[2] + sin_alpha * (cos_phi * u[2] + sin_phi * v[2])
    points['phi'] = np.atan2(points['y'], points['x'])
    points['theta'] = np.arccos(points['z'])

    return points

def make_circle_projection(azimuths: NDArray, zeniths: NDArray) -> NDArray:
    """
    Returns star point projections array.

    :param azimuths: azimuth coordinates of circle points
    :param zeniths: zenith coordinates of circle points
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
