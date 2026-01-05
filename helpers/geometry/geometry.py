"""Module with astronomical geometrical functions."""
from typing import Tuple, Union

from helpers.time.time import vequinox_hour_angle
from numpy.typing import NDArray
import numpy as np
from hip_catalog.hip_catalog import CatalogConstraints


def mag_to_radius(
        magnitude: Union[float, NDArray],
        constraints: CatalogConstraints,
) -> Union[float, NDArray]:
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

def get_horizontal_coords(config: dict, data: NDArray) -> Tuple[NDArray, NDArray]:
    """
    Get horizontal coordinates from catalog data.

    :param config: place configuration
    :param data: data to make conversion into horizontal coordinates
    :return: tuple of mask and horizontal coordinates with zenith distances, azimuths
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

    valid_mask = (horizontal_coords['zenith'] <= (np.pi / 2))

    return valid_mask, horizontal_coords

def make_stereo_projection(view_data: NDArray, constraints: CatalogConstraints) -> NDArray:
    """
    Returns point stereographic projections array.

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

    points_data = np.zeros(len(view_data), dtype=PROJECTION_DTYPE)
    points_data['size'] = mag_to_radius(view_data['v_mag'], constraints)
    points_data['radius'] = 2 * np.tan(view_data['zenith'] / 2.0)
    points_data['angle'] = view_data['azimuth']

    points_data['id'] = view_data['id']

    return points_data

def make_pinhole_projection(shot_condition: dict, camera_config: dict, data: NDArray) -> Tuple[NDArray, NDArray]:
    """

    :param shot_condition:
    :param camera_config:
    :param data:
    :return:
    """

    PICTURE_PLANE_DTYPE = np.dtype([
        ('x_pix', np.float32),
        ('y_pix', np.float32),
    ])
    picture_coords = np.zeros(len(data), dtype=PICTURE_PLANE_DTYPE)

    # Transform to camera coordinates
    rotation_eci_to_cam = create_camera_frame_system(
        center_dir=shot_condition['center_dir'],
        tilt_dec=shot_condition['tilt_angle']
    )
    eci_coords = np.column_stack([data['x'], data['y'], data['z']]).T
    points_cam = rotation_eci_to_cam @ eci_coords   # (N, 3)

    # Perspective projection
    x_proj = -camera_config['foc_len'] * points_cam[0, :] / points_cam[2, :]
    y_proj = -camera_config['foc_len'] * points_cam[1, :] / points_cam[2, :]

    # Convert to pixel coordinates
    # Origin at center, X right, Y up
    picture_coords['x_pix'] = x_proj + camera_config['width'] / 2
    picture_coords['y_pix'] = y_proj + camera_config['height'] / 2

    # Check if points are within image bounds
    in_bounds = ((picture_coords['x_pix'] >= 0) & (picture_coords['x_pix'] < camera_config['width']) &
                 (picture_coords['y_pix'] >= 0) & (picture_coords['y_pix'] < camera_config['height']))
    valid_mask = (points_cam[2, :] < 0) & in_bounds

    return valid_mask, picture_coords


def create_camera_frame_system(center_dir, tilt_dec):
    """
    Create camera coordinate system from shot conditions.
    :param center_dir: camera view direction
    :param tilt_dec: tilt angle of frame with respect to zenith direction
    :return: camera frame system matrix
    """

    # Z-axis: pointing direction (negative because camera looks along negative Z)
    z_axis = -center_dir
    z_axis /= np.linalg.norm(z_axis)

    # Define ECI z-axis
    up_vec = np.array([0.0, 0.0, 1.0])
    # If view is close to zenith choose y-axis
    if np.isclose(abs(z_axis[2]), 1.0):
        up_vec = np.array([0.0, 1.0, 0.0])

    # x-axis: right direction
    x_axis = np.cross(up_vec, z_axis)
    x_axis /= np.linalg.norm(x_axis)

    # y-axis: up direction in camera frame
    y_axis = np.cross(z_axis, x_axis)
    y_axis /= np.linalg.norm(y_axis)

    # Apply tilt rotation around Z-axis
    tilt_rad = np.deg2rad(tilt_dec)
    cos_tilt = np.cos(tilt_rad)
    sin_tilt = np.sin(tilt_rad)

    x_axis_rot = cos_tilt * x_axis + sin_tilt * y_axis
    y_axis_rot = -sin_tilt * x_axis + cos_tilt * y_axis

    # Rotation matrix from ECI to camera frame
    return np.vstack([x_axis_rot, y_axis_rot, z_axis])

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

    phi = np.linspace(0, 2 * np.pi, num_points, endpoint=True)
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

def make_circle_stereo_projection(azimuths: NDArray, zeniths: NDArray) -> NDArray:
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

    points_data = np.zeros(len(azimuths), dtype=PROJECTION_DTYPE)
    points_data['radius'] = 2 * np.tan(zeniths / 2.0)
    points_data['angle'] = azimuths

    return points_data

