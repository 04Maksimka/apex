"""Module with astronomical geometrical functions."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple, Union

import numpy as np
from matplotlib.collections import LineCollection
from numpy.typing import NDArray

from astrageek.helpers.time.time import vequinox_hour_angle


def _orthonormal_basis(v: NDArray) -> Tuple[NDArray, NDArray, NDArray]:
    """
    Make orthonormal basis (u, w, v_norm),
    where u is orthogonal to v_norm and w = v_norm cross u.

    :param v: vector
    :type v: NDArray
    :return: u, w, v_norm
    :rtype: tuple
    """

    v = np.asarray(v, dtype=float)
    v_norm = v / np.linalg.norm(v)

    if abs(v_norm[0]) < abs(v_norm[1]):
        if abs(v_norm[0]) < abs(v_norm[2]):
            a = np.array([1.0, 0.0, 0.0])
        else:
            a = np.array([0.0, 0.0, 1.0])
    else:
        if abs(v_norm[1]) < abs(v_norm[2]):
            a = np.array([0.0, 1.0, 0.0])
        else:
            a = np.array([0.0, 0.0, 1.0])

    u = a - np.dot(a, v_norm) * v_norm
    u /= np.linalg.norm(u)
    w = np.cross(v_norm, u)
    return u, w, v_norm


def rotate_direction_random(vec: NDArray, fov_deg: float) -> NDArray:
    """
    Rotates a vector by an arbitrary angle within a cone
    with an angle of fov in the direction of the original vector

    :param vec: initial vector
    :type vec: NDArray
    :param fov_deg: maximum angle
    :type fov_deg: float
    :return: rotated vector
    :rtype: NDArray
    """

    vec = np.asarray(vec, dtype=float)
    orig_norm = np.linalg.norm(vec)
    if np.isclose(orig_norm, 0.0):
        return np.zeros(3)

    u, w, v = _orthonormal_basis(vec)

    theta_max = np.deg2rad(fov_deg)
    cos_theta = np.random.uniform(np.cos(theta_max), 1.0)
    sin_theta = np.sqrt(1.0 - cos_theta**2)
    phi = np.random.uniform(0.0, 2.0 * np.pi)

    # cone direction
    d = v * cos_theta + (u * np.cos(phi) + w * np.sin(phi)) * sin_theta

    return d * orig_norm


def _wrap_ra(ra_deg: float, ra_center: float) -> float:
    """Wrap RA value so that it is within [ra_center - 180, ra_center + 180).
    This ensures continuity of lines that cross the RA boundary.

    :param ra_deg: RA in degrees (can be any value)
    :type ra_deg: float
    :param ra_center: Center of the RA display range in degrees
    :type ra_center: float
    :return: Wrapped RA value
    :rtype: float
    """
    diff = ra_deg - ra_center
    diff = (diff + 180.0) % 360.0 - 180.0
    return ra_center + diff


def _split_segments_at_boundary(
    ra_points: NDArray,
    dec_points: NDArray,
    ra_min: float,
    ra_max: float,
    dec_min: float,
    dec_max: float,
    ra_wrap_threshold: float = 180.0,
) -> List[NDArray]:
    """
    Split a continuous curve into segments, breaking at points where the curve
    jumps across the RA wrap boundary or goes out of the dec range.
    Also clips segments to the visible area, interpolating boundary crossings.

    :param ra_points: Array of RA values in degrees
    :type ra_points: NDArray
    :param dec_points: Array of Dec values in degrees
    :type dec_points: NDArray
    :param ra_min: Minimum RA of display range
    :type ra_min: float
    :param ra_max: Maximum RA of display range
    :type ra_max: float
    :param dec_min: Minimum Dec of display range
    :type dec_min: float
    :param dec_max: Maximum Dec of display range
    :type dec_max: float
    :param ra_wrap_threshold: Maximum allowed RA jump before splitting
    :type ra_wrap_threshold: float

    :return: List of Nx2 arrays, each representing
        a continuous segment [[ra, dec], ...]
    :rtype: List[NDArray]
    """

    if len(ra_points) < 2:
        return []

    segments = []
    current_segment = []

    for i in range(len(ra_points)):
        ra = ra_points[i]
        dec = dec_points[i]

        # Check if point is within dec range
        in_dec = dec_min <= dec <= dec_max
        # Check if point is within ra range
        in_ra = ra_min <= ra <= ra_max

        if i > 0:
            # Detect large RA jump (wrap-around)
            ra_jump = abs(ra - ra_points[i - 1])
            if ra_jump > ra_wrap_threshold:
                # Break segment here — interpolate exit and entry points
                if len(current_segment) >= 1:
                    # Interpolate the boundary crossing
                    prev_ra = ra_points[i - 1]
                    prev_dec = dec_points[i - 1]
                    curr_ra = ra
                    curr_dec = dec

                    # Determine which boundary was crossed
                    boundary_points = _interpolate_ra_wrap(
                        prev_ra, prev_dec, curr_ra, curr_dec, ra_min, ra_max
                    )

                    if boundary_points is not None:
                        exit_ra, exit_dec, entry_ra, entry_dec = (
                            boundary_points
                        )

                        # Add exit point to current segment
                        if dec_min <= exit_dec <= dec_max:
                            current_segment.append([exit_ra, exit_dec])

                        # Finalize current segment
                        if len(current_segment) >= 2:
                            segments.append(np.array(current_segment))
                        current_segment = []

                        # Start new segment with entry point
                        if dec_min <= entry_dec <= dec_max:
                            current_segment.append([entry_ra, entry_dec])
                    else:
                        if len(current_segment) >= 2:
                            segments.append(np.array(current_segment))
                        current_segment = []
                else:
                    current_segment = []

                # Add current point if in range
                if in_dec and in_ra:
                    current_segment.append([ra, dec])
                continue

        if in_dec and in_ra:
            if len(current_segment) == 0 and i > 0:
                # Interpolate entry from out-of-range to in-range
                prev_ra = ra_points[i - 1]
                prev_dec = dec_points[i - 1]
                edge_point = _interpolate_dec_boundary(
                    prev_ra, prev_dec, ra, dec, dec_min, dec_max
                )
                if edge_point is not None:
                    current_segment.append(edge_point)

            current_segment.append([ra, dec])
        else:
            if len(current_segment) >= 1:
                # Interpolate exit point
                prev_ra = ra_points[i - 1] if i > 0 else ra
                prev_dec = dec_points[i - 1] if i > 0 else dec
                if len(current_segment) > 0:
                    prev_ra = current_segment[-1][0]
                    prev_dec = current_segment[-1][1]
                edge_point = _interpolate_dec_boundary(
                    prev_ra, prev_dec, ra, dec, dec_min, dec_max
                )
                if edge_point is not None:
                    current_segment.append(edge_point)

                if len(current_segment) >= 2:
                    segments.append(np.array(current_segment))
                current_segment = []

    # Finalize last segment
    if len(current_segment) >= 2:
        segments.append(np.array(current_segment))

    return segments


def _interpolate_ra_wrap(
    ra1: float,
    dec1: float,
    ra2: float,
    dec2: float,
    ra_min: float,
    ra_max: float,
) -> Optional[Tuple[float, float, float, float]]:
    """Interpolate the point where a line segment crosses the RA wrap boundary.

    :param ra1: Right ascension of the start point
    :type ra1: float
    :param dec1: Declination of the start point
    :type dec1: float
    :param ra2: Right ascension of the end point
    :type ra2: float
    :param dec2: Declination of the end point
    :type dec1: float
    :param ra_min: Right ascension low boundary
    :type ra_min: float
    :param ra_max: Right ascension high boundary
    :type ra_max: float

    :return: interpolation result in format (exit_ra, exit_dec,
        entry_ra, entry_dec)
    :rtype: Tuple[float, float, float, float] | None
    """

    # Determine direction of wrap
    if ra1 > ra2:
        # Wrapping from high RA to low RA (crossing ra_max -> ra_min)
        # The "real" ra2 is ra2 + 360
        ra2_unwrapped = ra2 + 360.0
        # Fraction along segment where RA = ra_max
        if abs(ra2_unwrapped - ra1) < 1e-10:
            return None
        t = (ra_max - ra1) / (ra2_unwrapped - ra1)
        t = np.clip(t, 0, 1)
        dec_at_boundary = dec1 + t * (dec2 - dec1)
        return ra_max, dec_at_boundary, ra_min, dec_at_boundary
    else:
        # Wrapping from low RA to high RA (crossing ra_min -> ra_max)
        ra1_unwrapped = ra1 + 360.0
        if abs(ra1_unwrapped - ra2) < 1e-10:
            return None
        t = (ra_max - ra2) / (ra1_unwrapped - ra2)
        t = np.clip(t, 0, 1)
        dec_at_boundary = dec2 + t * (dec1 - dec2)
        return ra_min, dec_at_boundary, ra_max, dec_at_boundary


def _interpolate_dec_boundary(
    ra1: float,
    dec1: float,
    ra2: float,
    dec2: float,
    dec_min: float,
    dec_max: float,
) -> Optional[List[float]]:
    """Linear interpolation the point where a line crosses a dec boundary.

    :param ra1: Right ascension of the start point
    :type ra1: float
    :param dec1: Declination of the start point
    :type dec1: float
    :param ra2: Right ascension of the end point
    :type ra2: float
    :param dec2: Declination of the end point
    :type dec1: float
    :param dec_min: Declination low boundary
    :type dec_min: float
    :param dec_max: Declination high boundary
    :type dec_max: float

    :return: interpolation result in format [ra, dec] -- intersection point
    :rtype: List[float] | None

    """
    if abs(dec2 - dec1) < 1e-10:
        return None

    # Check which boundary is crossed
    for boundary in [dec_min, dec_max]:
        t = (boundary - dec1) / (dec2 - dec1)
        if 0.0 <= t <= 1.0:
            ra_at_boundary = ra1 + t * (ra2 - ra1)
            return [ra_at_boundary, boundary]

    return None


def _make_pair_segments_with_wrapping(
    ra1: float,
    dec1: float,
    ra2: float,
    dec2: float,
    ra_min: float,
    ra_max: float,
    ra_wrap_threshold: float = 180.0,
) -> List[NDArray]:
    """Create line segments for a pair of points, handling RA wrap-around.
    If the RA difference is larger than the threshold, splits into two segments
    that go to opposite edges of the frame.

    :param ra1: Right ascension of the first point
    :type ra1: float
    :param dec1: Declination of the first point
    :type dec1: float
    :param ra2: Right ascension of the second point
    :type ra2: float
    :param dec2: Declination of the second point
    :type dec1: float
    :param ra_min: Right ascension low boundary
    :type ra_min: float
    :param ra_max: Right ascension high boundary
    :type ra_max: float
    :param ra_wrap_threshold: Maximum allowed RA difference
    :type ra_wrap_threshold: float (Default value = 180.0)

    :return: List of Nx2 arrays representing line segments
    :rtype: List[NDArray]
    """
    ra_diff = abs(ra2 - ra1)

    if ra_diff <= ra_wrap_threshold:
        # No wrapping needed — single segment
        return [np.array([[ra1, dec1], [ra2, dec2]])]

    # Wrapping needed — split into two segments
    boundary_points = _interpolate_ra_wrap(
        ra1, dec1, ra2, dec2, ra_min, ra_max
    )
    if boundary_points is None:
        return [np.array([[ra1, dec1], [ra2, dec2]])]

    exit_ra, exit_dec, entry_ra, entry_dec = boundary_points

    segments = [
        np.array(
            [[ra1, dec1], [exit_ra, exit_dec]]
        ),  # Segment from point1 to exit boundary
        np.array(
            [[entry_ra, entry_dec], [ra2, dec2]]
        ),  # Segment from entry boundary to point2
    ]

    return segments


def generate_random_direction() -> NDArray:
    """Generate random unit vector for sky direction."""

    theta = np.random.uniform(0, 2 * np.pi)  # azimuth
    phi = np.arccos(np.random.uniform(-1, 1))  # polar angle

    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)

    return np.array([x, y, z], dtype=np.float32)


def angular_distance(axis: NDArray, vectors: NDArray) -> float:
    """
    Angular distance between vectors and axis

    :param axis: the vector from which the distance is being calculated
    :type axis: NDArray
    :param vectors: the vectors being calculated):
    :type vectors: NDArray

    :return: angular distance between vectors and axis
    :rtype: float
    """

    axis = np.asarray(axis, dtype=np.float64)
    vectors = np.asarray(vectors, dtype=np.float64)

    axis_unit = axis / np.linalg.norm(axis)

    # Normalize vectors
    vec_norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(vec_norms == 0):
        raise ValueError("Vectors cannot contain zero vectors")
    vecs_normalized = vectors / vec_norms

    # Calculate angular distance using dot product
    cos_theta = np.dot(vecs_normalized, axis_unit)

    angular_dists = np.arccos(cos_theta)

    return angular_dists


def mag_to_radius(
    magnitude: Union[float, NDArray],
    max_magnitude: float,
    min_magnitude: float,
) -> Union[float, NDArray]:
    """
    Returns radius of the point corresponds to given star magnitude.

    :param magnitude: star magnitude(s)
    :type magnitude: float or NDArray
    :param max_magnitude: maximum magnitude
    :type max_magnitude: float
    :param min_magnitude: minimum magnitude
    :type min_magnitude: float

    :return: star image radius
    :rtype: float or NDArray
    """

    if min_magnitude is None:
        radii = np.maximum(max_magnitude - magnitude, 0.0)
    else:
        radii = (max_magnitude - magnitude) / (max_magnitude - min_magnitude)
    return radii**1.3


def get_horizontal_coords(
    longitude: float, latitude: float, local_time: datetime, data: NDArray
) -> Tuple[NDArray, NDArray]:
    """
    Get horizontal coordinates from catalog data.

    :param longitude: place longitude
    :type longitude: float
    :param latitude: place latitude
    :type latitude: float
    :param local_time: local time
    :type local_time: datetime
    :param data: data to make conversion into horizontal coordinates
    :type data: NDArray

    :return: a pair of mask and horizontal coordinates
        with zenith distances, azimuths
    :rtype: tuple
    """

    HORIZONTAL_DTYPE = np.dtype(
        [
            ("x", np.float32),
            ("y", np.float32),
            ("z", np.float32),
            ("azimuth", np.float32),
            ("zenith", np.float32),
        ]
    )

    # Get ECI star coordinates
    eci_coords = np.column_stack([data["x"], data["y"], data["z"]]).T

    # Calculate local sidereal time
    sidereal_time = vequinox_hour_angle(longitude=longitude, local=local_time)

    # Rotate ECI (XYZ) to "cartesian" equatorial system (X'Y'Z'),
    # so Z' is directed to the North celestial pole, X' --- to the West point
    sl = np.sin(latitude)
    cl = np.cos(latitude)
    st = np.sin(sidereal_time)
    ct = np.cos(sidereal_time)
    rotation_latitude = np.array(
        [[1.0, 0.0, 0.0], [0.0, sl, -cl], [0.0, cl, sl]]
    )
    rotation_time = np.array([[st, -ct, 0.0], [ct, st, 0.0], [0.0, 0.0, 1.0]])
    rotation_matrix = rotation_latitude @ rotation_time
    cartesian_hor_coords = rotation_matrix @ eci_coords

    # 0, 1, 2 is x, y, z below
    horizontal_coords = np.zeros(eci_coords.shape[1], dtype=HORIZONTAL_DTYPE)
    horizontal_coords["x"] = cartesian_hor_coords[0, :]
    horizontal_coords["y"] = cartesian_hor_coords[1, :]
    horizontal_coords["z"] = cartesian_hor_coords[2, :]
    horizontal_coords["azimuth"] = np.atan2(
        cartesian_hor_coords[0, :], cartesian_hor_coords[1, :]
    )
    horizontal_coords["zenith"] = np.arccos(cartesian_hor_coords[2, :])

    valid_mask = horizontal_coords["zenith"] <= (np.pi / 1.9)

    return valid_mask, horizontal_coords


def make_stereo_projection(view_data: NDArray) -> NDArray:
    """
    Returns point stereographic projections array.

    :param view_data: observed object parameters in horizontal coordinates
    :type view_data: NDArray

    :return: image point parameters
    :rtype: NDArray
    """

    PROJECTION_DTYPE = np.dtype(
        [
            ("size", np.float32),
            ("radius", np.float32),
            ("angle", np.float32),
            ("v_mag", np.float32),
            ("id", np.int32),
        ]
    )

    points_data = np.zeros(len(view_data), dtype=PROJECTION_DTYPE)
    points_data["radius"] = 2 * np.tan(view_data["zenith"] / 2.0)
    points_data["angle"] = view_data["azimuth"]
    points_data["v_mag"] = view_data["v_mag"]
    points_data["id"] = view_data["id"]

    return points_data


def make_pinhole_projection(
    center_direction: NDArray,
    tilt_dec: float,
    focal_length: float,
    image_width: float,
    image_height: float,
    data: NDArray,
) -> Tuple[NDArray, NDArray]:
    """
    Returns point pinhole projections array.

    :param center_direction: ECI unit vector of view direction
    :type center_direction: NDArray
    :param tilt_dec: frame tilt angle in degrees
    :type tilt_dec: float
    :param focal_length: focal length in pixels
    :type focal_length: float
    :param image_width: frame width in pixels
    :type image_width: float
    :param image_height: frame height in pixels
    :type image_height: float
    :param data: data to project
    :type data: NDArray

    :return: a pair of mask and coordinates in reference plane system
    :rtype: tuple
    """

    PICTURE_PLANE_DTYPE = np.dtype(
        [
            ("x_pix", np.float32),
            ("y_pix", np.float32),
        ]
    )
    picture_coords = np.zeros(len(data), dtype=PICTURE_PLANE_DTYPE)

    # Transform to camera coordinates
    rotation_eci_to_cam = create_camera_frame_system(
        center_direction=center_direction, tilt_dec=tilt_dec
    )
    eci_coords = np.column_stack([data["x"], data["y"], data["z"]]).T
    points_cam = rotation_eci_to_cam @ eci_coords  # (N, 3)

    # Perspective projection
    x_proj = -focal_length * points_cam[0, :] / points_cam[2, :]
    y_proj = -focal_length * points_cam[1, :] / points_cam[2, :]

    # Convert to pixel coordinates
    # Origin at center, X right, Y up
    picture_coords["x_pix"] = x_proj + image_width / 2
    picture_coords["y_pix"] = y_proj + image_height / 2

    # Check if points are within image bounds
    gap = 1 / 16
    in_bounds = (
        (picture_coords["x_pix"] >= -image_width * gap)
        & (picture_coords["x_pix"] <= image_width * (1 + gap))
        & (picture_coords["y_pix"] >= -image_height * gap)
        & (picture_coords["y_pix"] <= image_height * (1 + gap))
    )
    valid_mask = (points_cam[2, :] < 0) & in_bounds

    return valid_mask, picture_coords


def create_camera_frame_system(
    center_direction: NDArray, tilt_dec: float
) -> NDArray:
    """
    Create camera coordinate system from shot conditions.

    :param center_direction: ECI unit vector of camera view direction
    :type center_direction: NDArray
    :param tilt_dec: tilt angle of frame with respect to zenith direction
    :type tilt_dec: float

    :return: camera frame system matrix
    :rtype: NDArray
    """

    # Z-axis:
    # pointing direction (negative because camera looks along negative Z)
    z_axis = -center_direction
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


def generate_small_circle(
    spheric_normal_deg: NDArray, alpha_deg: float, num_points: int
) -> NDArray:
    """
    Generate a small circle on unit sphere in ECI coordinates.

    :param spheric_normal_deg: spherical coordinates
        on the normal to hte place of circle, angles in degrees
    :type spheric_normal_deg: NDArray
    :param alpha_deg: angle between any radis vector
        of the point on small circle and normal
    :type alpha_deg: float
    :param num_points: number of points to generate
    :type num_points: int

    :return: array of points in cartesian ECI coordinates
    :rtype: NDArray
    """

    POINTS_DTYPE = np.dtype(
        [
            ("x", np.float32),
            ("y", np.float32),
            ("z", np.float32),
            ("zenith", np.float32),
            ("azimuth", np.float32),
        ]
    )

    # Extract angles, convert to radians
    theta = np.deg2rad(spheric_normal_deg[0])
    phi = np.deg2rad(spheric_normal_deg[1])

    # Define normal in cartesian coordinates
    normal = np.array(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ]
    )

    # Define ECI z-axis
    up_vec = np.array([0.0, 0.0, 1.0])
    # If normal is close to zenith axis choose y-axis
    if np.isclose(abs(normal[2]), 1.0):
        up_vec = np.array([1.0, 0.0, 0.0])

    u = np.cross(up_vec, normal)
    u /= np.linalg.norm(u)

    v = np.cross(normal, u)
    v /= np.linalg.norm(v)

    phi = np.linspace(0, 2 * np.pi, num_points, endpoint=True)
    alpha_rad = np.deg2rad(alpha_deg)
    cos_alpha = np.cos(alpha_rad)
    sin_alpha = np.sin(alpha_rad)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)

    points = np.zeros(num_points, dtype=POINTS_DTYPE)
    points["x"] = cos_alpha * normal[0] + sin_alpha * (
        cos_phi * u[0] + sin_phi * v[0]
    )
    points["y"] = cos_alpha * normal[1] + sin_alpha * (
        cos_phi * u[1] + sin_phi * v[1]
    )
    points["z"] = cos_alpha * normal[2] + sin_alpha * (
        cos_phi * u[2] + sin_phi * v[2]
    )
    points["azimuth"] = np.atan2(points["y"], points["x"])
    points["zenith"] = np.arccos(points["z"])

    return points


def make_points_stereo_projection(points: NDArray) -> NDArray:
    """
    Returns star point projections array.

    :param points: points to project, must contain azimuth and zenith args
    :type points: NDArray

    :return: projection point polar coordinates
    :rtype: NDArray
    """

    PROJECTION_DTYPE = np.dtype(
        [
            ("radius", np.float32),
            ("angle", np.float32),
        ]
    )

    points_data = np.zeros(len(points), dtype=PROJECTION_DTYPE)
    points_data["radius"] = 2 * np.tan(points["zenith"] / 2.0)
    points_data["angle"] = points["azimuth"]

    return points_data


def make_equatorial_grid_pinhole(
    center_direction: NDArray,
    tilt_dec: float,
    focal_length: float,
    image_width: float,
    image_height: float,
    grid_step_dec: float,
    grid_step_ra: float,
) -> LineCollection:
    """
    Creates an equatorial grid for pinhole image/

    :param center_direction: ECI unit vector of camera view direction
    :type center_direction: NDArray
    :param tilt_dec: tilt angle in degrees
    :type tilt_dec: float
    :param focal_length: focal length in pixels
    :type focal_length: float
    :param image_width: image width in pixels
    :type image_width: float
    :param image_height: image height in pixels
    :type image_height: float
    :param grid_step_dec: declination grid step in degrees
    :type grid_step_dec: float
    :param grid_step_ra: right ascension grid step in degrees
    :type grid_step_ra: float

    :return: grid as LineCollection object
    :rtype: LineCollection
    """

    num_points = 100
    gap_threshold = np.pi / num_points

    fov_rad = 2 * np.arctan(
        np.sqrt(image_width**2 + image_height**2) / (2 * focal_length)
    )

    polar_distances = np.arange(0, 180, grid_step_dec, dtype=np.float64)
    right_ascensions = np.arange(0, 180, grid_step_ra, dtype=np.float64)
    array_grid = []

    # Draw azimuthal great circles
    for ra in right_ascensions:
        circle = generate_small_circle(
            spheric_normal_deg=np.array([90.0, ra + 90.0]),
            alpha_deg=90.0,
            num_points=num_points,
        )
        good_circle = clean_far_points(
            circle=circle,
            fov_rad=fov_rad,
            center_direction=center_direction,
            gap_threshold=gap_threshold,
        )
        _, projection = make_pinhole_projection(
            center_direction=center_direction,
            tilt_dec=tilt_dec,
            image_width=image_width,
            image_height=image_height,
            focal_length=focal_length,
            data=good_circle,
        )
        array_grid.append(
            np.column_stack(
                [
                    projection["x_pix"].astype(np.float64),
                    projection["y_pix"].astype(np.float64),
                ]
            )
        )
    # Draw zenith small circles
    for p in polar_distances:
        circle = generate_small_circle(
            spheric_normal_deg=np.array([0.0, 0.0]),
            alpha_deg=p,
            num_points=num_points,
        )
        good_circle = clean_far_points(
            circle=circle,
            fov_rad=fov_rad,
            center_direction=center_direction,
            gap_threshold=gap_threshold,
        )
        _, projection = make_pinhole_projection(
            center_direction=center_direction,
            tilt_dec=tilt_dec,
            image_width=image_width,
            image_height=image_height,
            focal_length=focal_length,
            data=good_circle,
        )

        array_grid.append(
            np.column_stack(
                [
                    projection["x_pix"].astype(np.float64),
                    projection["y_pix"].astype(np.float64),
                ]
            )
        )

    grid = LineCollection(
        segments=array_grid,
        label="Equatorial grid",
        colors="magenta",
        alpha=0.25,
        linewidth=0.5,
    )

    return grid


def clean_far_points(
    circle: NDArray,
    fov_rad: float,
    center_direction: NDArray,
    gap_threshold: float,
) -> NDArray:
    """
    Removes points further than FOV from center direction out of circle

    :param circle: circle initial points to clean
    :type circle: NDArray
    :param fov_rad: camera field of view
    :type fov_rad: float
    :param center_direction: ECI unit vector of camera view direction
    :type center_direction: NDArray
    :param gap_threshold:
        threshold to consider distance a large gap between points
    :type gap_threshold: float

    :return: cleaned points
    :rtype: NDArray
    """

    max_distance = fov_rad / 2

    points = np.column_stack([circle["x"], circle["y"], circle["z"]])
    distances = angular_distance(center_direction, points)
    mask = distances <= max_distance
    filtered_circle = circle[mask]

    if len(filtered_circle) <= 2:
        return filtered_circle

    filtered_points = np.column_stack(
        [filtered_circle["x"], filtered_circle["y"], filtered_circle["z"]]
    )

    # Sort points
    azimuth = np.arctan2(filtered_points[:, 1], filtered_points[:, 0])
    if np.isclose(np.std(azimuth), 0.0):
        # For meridians sort by zenith distance
        zenith = np.arccos(filtered_points[:, 2])
        sort_indices = np.argsort(zenith)
    else:
        # For parallels sort by azimuth
        sort_indices = np.argsort(azimuth)

    filtered_circle_sorted = filtered_circle[sort_indices]
    filtered_points_sorted = filtered_points[sort_indices]

    n = len(filtered_points_sorted)
    if n <= 2:
        return filtered_circle_sorted

    # Calculate distances between neigbour points
    points_i = filtered_points_sorted
    points_j = np.roll(filtered_points_sorted, -1, axis=0)
    dot_products = np.sum(points_i * points_j, axis=1)
    dot_products = np.clip(dot_products, -1.0, 1.0)
    angles = np.arccos(dot_products)

    # Search for big gaps
    large_gap_mask = angles > gap_threshold

    if not np.any(large_gap_mask):
        return filtered_circle_sorted

    # Maximum gap
    max_gap_idx = np.argmax(angles)
    if angles[max_gap_idx] <= gap_threshold:
        return filtered_circle_sorted

    # Roll array
    shift_amount = -(max_gap_idx + 1)
    rolled_circle = np.roll(filtered_circle_sorted, shift_amount, axis=0)

    return rolled_circle
