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

    def __post_init__(self):
        # Normalize direction vector
        self.center_dir /= np.linalg.norm(self.center_dir)


@dataclass
class CameraCfg:
    """Camera configurations."""
    width: int  # pix
    height: int  # pix
    foc_len: float  # pix (focal length)

    @classmethod
    def from_fov_and_aspect(
            cls,
            fov_deg: float,
            aspect_ratio: float,
            height_pix: int,
    ):
        """
        Create CameraCfg from field of view and aspect ratio.

        :param fov_deg: Horizontal field of view in degrees
        :param aspect_ratio: Width/height ratio
        :param height_pix: Height in pixels
        """
        width_pix = int(height_pix * aspect_ratio)
        # Calculate focal length from FOV
        fov_rad = np.deg2rad(fov_deg)
        foc_len_pix = (width_pix / 2) / np.tan(fov_rad / 2)

        return cls(width=width_pix, height=height_pix, foc_len=foc_len_pix)


@dataclass
class ProjectionResult:
    """Result of pinhole projection."""
    stars: NDArray  # Structured array with star projections
    planets: NDArray  # Structured array with planet projections


class Pinhole:
    """Pinhole camera projector."""

    def __init__(
            self,
            shot_cond: ShotConditions,
            camera_cfg: CameraCfg,
            time: datetime,
            catalog: Catalog,
            planet_catalog: PlanetCatalog
    ):
        """
        Initialize pinhole projector.

        :param shot_cond: Shot conditions
        :param camera_cfg: Camera configuration
        :param time: Observation time
        :param catalog: Star catalog instance
        :param planet_catalog: Planet catalog instance
        """

        self.shot_cond = shot_cond
        self.camera_cfg = camera_cfg
        self.time = time
        self.catalog = catalog
        self.planet_catalog = planet_catalog

        # Create camera coordinate system
        self._create_camera_frame_system()

    def _create_camera_frame_system(self):
        """Create camera coordinate system from shot conditions."""

        # Z-axis: pointing direction (negative because camera looks along negative Z)
        z_axis = -self.shot_cond.center_dir

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
        tilt_rad = np.deg2rad(self.shot_cond.tilt_angle)
        cos_tilt = np.cos(tilt_rad)
        sin_tilt = np.sin(tilt_rad)

        x_axis_rot = cos_tilt * x_axis + sin_tilt * y_axis
        y_axis_rot = -sin_tilt * x_axis + cos_tilt * y_axis

        # Rotation matrix from ECI to camera frame
        self.R_eci_to_cam = np.vstack([x_axis_rot, y_axis_rot, z_axis])

    def _project_points(self, points_eci: NDArray) -> Tuple[NDArray, NDArray]:
        """
        Project ECI points to image plane.

        :param points_eci: (N, 3) array of unit vectors in ECI

        :return: Tuple of (valid_mask, pixel_coords) where:
            - valid_mask: boolean array of points in front of camera
            - pixel_coords: (N, 2) array of pixel coordinates
        """
        # Transform to camera coordinates
        points_cam = points_eci @ self.R_eci_to_cam.T  # (N, 3)

        # Check if points are in front of camera (z < 0 in camera coordinates)
        valid_mask = points_cam[:, 2] < 0

        # Perspective projection
        x_proj = self.camera_cfg.foc_len * points_cam[:, 0] / points_cam[:, 2]
        y_proj = self.camera_cfg.foc_len * points_cam[:, 1] / points_cam[:, 2]

        # Convert to pixel coordinates
        # Origin at center, X right, Y up
        x_pix = x_proj + self.camera_cfg.width / 2
        y_pix = y_proj + self.camera_cfg.height / 2

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
            constraints = CatalogConstraints(max_magnitude=6.0)

        stars_data = self.catalog.get_stars(constraints)

        # Extract ECI coordinates
        star_coords = np.column_stack([stars_data['x'],
                                       stars_data['y'],
                                       stars_data['z']])

        # Project stars
        valid_mask, pixel_coords = self._project_points(star_coords)

        # Create structured array with results
        RESULT_DTYPE = np.dtype(
            [
                ('x_pix', np.float32),
                ('y_pix', np.float32),
                ('v_mag', np.float32),
                ('ra', np.float32),
                ('dec', np.float32),
                ('hip_id', np.int32)
            ]
        )

        result = np.zeros(np.sum(valid_mask), dtype=RESULT_DTYPE)
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
        RESULT_DTYPE = np.dtype(
            [
                ('x_pix', np.float32),
                ('y_pix', np.float32),
                ('v_mag', np.float32),
                ('ra', np.float32),
                ('dec', np.float32),
                ('planet_id', np.int32)
            ]
        )

        result = np.zeros(np.sum(valid_mask), dtype=RESULT_DTYPE)
        result['x_pix'] = pixel_coords[valid_mask, 0]
        result['y_pix'] = pixel_coords[valid_mask, 1]
        result['v_mag'] = planets_data['v_mag'][valid_mask]
        result['ra'] = planets_data['ra'][valid_mask]
        result['dec'] = planets_data['dec'][valid_mask]
        result['planet_id'] = planets_data['planet_id'][valid_mask]

        return result

    def project(self, constraints: Optional[CatalogConstraints]=None) -> ProjectionResult:
        """Get pinhole projections of stars and planets."""
        stars = self.get_stars(constraints=constraints)
        planets = self.get_planets()

        return ProjectionResult(stars=stars, planets=planets)

