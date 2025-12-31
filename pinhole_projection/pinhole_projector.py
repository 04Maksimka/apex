"""Module with pinhole projector."""
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Optional
import numpy as np
from numpy.typing import NDArray

from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from planets_catalog.planet_catalog import PlanetCatalog


@dataclass
class ShotConditions:
    """Class of the shot conditions."""
    center_dir: NDArray  # direction in ECI (unit vector)
    tilt_angle: float  # angle in degrees on which we rotate a camera


@dataclass
class CameraCfg:
    """Camera configurations."""
    width: int  # pix
    height: int  # pix
    foc_len: float  # pix (focal length)


@dataclass
class ProjectionResult:
    """Result of pinhole projection."""
    stars: NDArray  # Structured array with star projections
    planets: NDArray  # Structured array with planet projections


class Pinhole:
    """Pinhole camera projector."""

    def __init__(self,
                 shot_cond: ShotConditions,
                 camera_cfg: CameraCfg,
                 time: datetime,
                 catalog: Catalog,
                 planet_catalog: PlanetCatalog):
        """
        Initialize pinhole projector.

        Args:
            shot_cond: Shot conditions
            camera_cfg: Camera configuration
            time: Observation time
            catalog: Star catalog instance
            planet_catalog: Planet catalog instance
        """
        self.shot_cond = shot_cond
        self.camera_cfg = camera_cfg
        self.time = time
        self.catalog = catalog
        self.planet_catalog = planet_catalog

        # Normalize center direction
        self.center_dir = shot_cond.center_dir / np.linalg.norm(
            shot_cond.center_dir)

        # Create camera coordinate system
        self._create_camera_frame()

    def _create_camera_frame(self):
        """Create camera coordinate system from shot conditions."""
        # Z-axis: pointing direction (negative because camera looks along negative Z)
        z_axis = -self.center_dir

        # Initial up vector (ECI Z-axis)
        up_vec = np.array([0, 0, 1])

        # Handle edge case when pointing near zenith
        if np.abs(np.dot(z_axis, up_vec)) > 0.99:
            up_vec = np.array([0, 1, 0])

        # X-axis: right direction (cross product of up and view direction)
        x_axis = np.cross(up_vec, z_axis)
        x_axis = x_axis / np.linalg.norm(x_axis)

        # Y-axis: up direction in camera frame
        y_axis = np.cross(z_axis, x_axis)
        y_axis = y_axis / np.linalg.norm(y_axis)

        # Apply tilt rotation around Z-axis
        tilt_rad = np.deg2rad(self.shot_cond.tilt_angle)
        cos_tilt = np.cos(tilt_rad)
        sin_tilt = np.sin(tilt_rad)

        # Rotate X and Y axes around Z axis
        x_axis_rot = cos_tilt * x_axis + sin_tilt * y_axis
        y_axis_rot = -sin_tilt * x_axis + cos_tilt * y_axis

        # Rotation matrix from ECI to camera frame
        self.R_eci_to_cam = np.vstack([x_axis_rot, y_axis_rot, z_axis])

    def _project_points(self, points_eci: NDArray) -> Tuple[NDArray, NDArray]:
        """
        Project ECI points to image plane.

        Args:
            points_eci: (N, 3) array of unit vectors in ECI

        Returns:
            Tuple of (valid_mask, pixel_coords) where:
            - valid_mask: boolean array of points in front of camera
            - pixel_coords: (N, 2) array of pixel coordinates
        """
        # Transform to camera coordinates
        points_cam = points_eci @ self.R_eci_to_cam.T  # (N, 3)

        # Check if points are in front of camera (z < 0 in camera coordinates)
        valid_mask = points_cam[:, 2] < 0

        # Perspective projection
        x_proj = -self.camera_cfg.foc_len * points_cam[:, 0] / points_cam[:, 2]
        y_proj = -self.camera_cfg.foc_len * points_cam[:, 1] / points_cam[:, 2]

        # Convert to pixel coordinates
        # Origin at center, X right, Y up
        x_pix = x_proj + self.camera_cfg.width / 2
        y_pix = -y_proj + self.camera_cfg.height / 2  # Flip Y axis

        pixel_coords = np.column_stack([x_pix, y_pix])

        # Check if points are within image bounds
        in_bounds = ((x_pix >= 0) & (x_pix < self.camera_cfg.width) &
                     (y_pix >= 0) & (y_pix < self.camera_cfg.height))
        valid_mask = valid_mask & in_bounds

        return valid_mask, pixel_coords

    def get_stars(self,
                  constraints: Optional[CatalogConstraints] = None) -> NDArray:
        """Get ECI coords of stars located in the field of view."""
        if constraints is None:
            constraints = CatalogConstraints(max_magnitude=5.5)

        stars_data = self.catalog.get_stars(constraints)

        # Extract ECI coordinates
        star_coords = np.column_stack([stars_data['x'],
                                       stars_data['y'],
                                       stars_data['z']])

        # Project stars
        valid_mask, pixel_coords = self._project_points(star_coords)

        # Create structured array with results
        dtype = [
            ('x_pix', 'f4'), ('y_pix', 'f4'),
            ('v_mag', 'f4'), ('ra', 'f4'), ('dec', 'f4'),
            ('hip_id', 'i4')
        ]

        result = np.zeros(np.sum(valid_mask), dtype=dtype)
        result['x_pix'] = pixel_coords[valid_mask, 0]
        result['y_pix'] = pixel_coords[valid_mask, 1]
        result['v_mag'] = stars_data['v_mag'][valid_mask]
        result['ra'] = stars_data['ra'][valid_mask]
        result['dec'] = stars_data['dec'][valid_mask]
        result['hip_id'] = stars_data['hip_id'][valid_mask]

        return result

    def get_planets(self) -> NDArray:
        """Get ECI coords of planets located in the field of view."""
        planets_data = self.planet_catalog.get_planets(self.time)

        # Extract ECI coordinates
        planet_coords = np.column_stack([planets_data['x'],
                                         planets_data['y'],
                                         planets_data['z']])

        # Project planets
        valid_mask, pixel_coords = self._project_points(planet_coords)

        # Create structured array with results
        dtype = [
            ('x_pix', 'f4'), ('y_pix', 'f4'),
            ('v_mag', 'f4'), ('ra', 'f4'), ('dec', 'f4'),
            ('planet_id', 'i4')
        ]

        result = np.zeros(np.sum(valid_mask), dtype=dtype)
        result['x_pix'] = pixel_coords[valid_mask, 0]
        result['y_pix'] = pixel_coords[valid_mask, 1]
        result['v_mag'] = planets_data['v_mag'][valid_mask]
        result['ra'] = planets_data['ra'][valid_mask]
        result['dec'] = planets_data['dec'][valid_mask]
        result['planet_id'] = planets_data['planet_id'][valid_mask]

        return result

    def project(self) -> ProjectionResult:
        """Get pinhole projections of stars and planets."""
        stars = self.get_stars()
        planets = self.get_planets()

        return ProjectionResult(stars=stars, planets=planets)
