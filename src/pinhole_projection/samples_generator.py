"""Generator of samples of pinhole projection for all constellations and random sky areas."""
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
from matplotlib import pyplot as plt

from src.helpers.geometry.geometry import generate_random_direction
from src.constellations_metadata.constellations_data import (
    get_available_constellations,
    get_constellation_center,
    get_constellation_name
)
from src.helpers.pdf_helpers.figure2pdf import save_figure_pinhole
from src.hip_catalog.hip_catalog import Catalog, CatalogConstraints
from src.pinhole_projection.pinhole_projector import (
    ShotConditions,
    CameraConfig,
    Pinhole,
    PinholeConfig,
    ConstellationConfig
)
from src.planets_catalog.planet_catalog import PlanetCatalog


def get_student_config(time: datetime) -> PinholeConfig:
    """Get configuration for student mode (minimal features).

    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime: 

    """
    return PinholeConfig(
        local_time=time,
        add_ecliptic=False,
        add_equator=False,
        add_galactic_equator=False,
        add_planets=False,
        add_ticks=False,
        add_equatorial_grid=False,
        use_dark_mode=False,
        add_constellations=False,
        add_constellations_names=False,
    )


def get_student_with_planets_config(time: datetime) -> PinholeConfig:
    """Get configuration for student mode with planets.

    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime: 

    """
    return PinholeConfig(
        local_time=time,
        add_ecliptic=False,
        add_equator=False,
        add_galactic_equator=False,
        add_planets=True,
        add_ticks=False,
        add_equatorial_grid=False,
        use_dark_mode=False,
        add_constellations=False,
        add_constellations_names=False,
    )


def get_teacher_config(time: datetime) -> PinholeConfig:
    """Get configuration for teacher mode (full features).

    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime:
    :param time: datetime: 

    """
    return PinholeConfig(
        local_time=time,
        add_ecliptic=True,
        add_equator=True,
        add_galactic_equator=True,
        add_planets=True,
        add_ticks=False,
        add_equatorial_grid=True,
        use_dark_mode=False,
        add_constellations=True,
        add_constellations_names=True,
    )

def render_and_save(
        shot_cond: ShotConditions,
        camera_cfg: CameraConfig,
        config: PinholeConfig,
        catalog: Catalog,
        planet_catalog: PlanetCatalog,
        constraints: CatalogConstraints,
        output_path: Path,
        constellation_config: Optional[ConstellationConfig] = None,
):
    """Render a pinhole projection and save it to PDF.

    :param shot_cond: Shot conditions (direction and tilt)
    :param camera_cfg: Camera configuration
    :param config: Pinhole configuration
    :param catalog: Star catalog
    :param planet_catalog: Planet catalog
    :param constraints: Catalog constraints
    :param output_path: Output file path
    :param constellation_config: Optional constellation configuration
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions:
    :param camera_cfg: CameraConfig:
    :param config: PinholeConfig:
    :param catalog: Catalog:
    :param planet_catalog: PlanetCatalog:
    :param constraints: CatalogConstraints:
    :param output_path: Path:
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)
    :param shot_cond: ShotConditions: 
    :param camera_cfg: CameraConfig: 
    :param config: PinholeConfig: 
    :param catalog: Catalog: 
    :param planet_catalog: PlanetCatalog: 
    :param constraints: CatalogConstraints: 
    :param output_path: Path: 
    :param constellation_config: Optional[ConstellationConfig]:  (Default value = None)

    """
    # Create pinhole projector
    pinhole = Pinhole(
        shot_cond=shot_cond,
        camera_cfg=camera_cfg,
        config=config,
        catalog=catalog,
        planet_catalog=planet_catalog,
        constellation_config=constellation_config,
    )

    # Generate projection
    fig, ax = pinhole.generate(constraints=constraints)
    ax.set_aspect('equal')

    # Save to PDF
    save_figure_pinhole(
        fig=fig,
        filename=str(output_path),
        logo_path="helpers/pdf_helpers/logo_astrageek.png",
        footer_text="Generated by AstraGeek - skychart.astrageek.ru",
        logo_position=(0.12, 0.97),
        text_position=(0.5, 0.01),
    )

    plt.close(fig)


def generate_constellation_samples(
        output_folder: str,
        time: datetime,
        fov_deg: float = 90.0,
        tilt_angle: float = 0.0,
        max_magnitude: float = 5.5,
):
    """Generate sample PDFs for all constellations.
    
    Each constellation gets a folder with three PDFs:
    1. student.pdf - basic view without annotations
    2. student_with_planets.pdf - view with planets
    3. teacher.pdf - full view with all annotations and constellations

    :param output_folder: Root folder for output
    :param time: Observation time
    :param fov_deg: Field of view in degrees
    :param tilt_angle: Camera tilt angle in degrees
    :param max_magnitude: Maximum star magnitude to display
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str:
    :param time: datetime:
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)
    :param output_folder: str: 
    :param time: datetime: 
    :param fov_deg: float:  (Default value = 90.0)
    :param tilt_angle: float:  (Default value = 0.0)
    :param max_magnitude: float:  (Default value = 5.5)

    """
    # Setup
    root = Path(output_folder) / "constellations"
    root.mkdir(parents=True, exist_ok=True)

    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=True)
    planet_catalog = PlanetCatalog()
    constraints = CatalogConstraints(max_magnitude=max_magnitude)

    # Camera configuration
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=1.5,
        height_pix=1000
    )

    # Get all constellations
    constellations = get_available_constellations()

    print(f"Generating samples for {len(constellations)} constellations...")

    for i, const_abbr in enumerate(constellations):
        const_name = get_constellation_name(const_abbr)
        print(
            f"[{i + 1}/{len(constellations)}] Processing {const_name} ({const_abbr})...")

        # Create constellation folder
        const_folder = root / f"{const_abbr}_{const_name.replace(' ', '_')}"
        const_folder.mkdir(exist_ok=True)

        # Get constellation center as shooting direction
        center_direction = np.asarray(
            get_constellation_center(const_abbr),
            dtype=np.float32
        )

        tilt_angle = np.random.uniform(-180.0, 180.0)

        shot_cond = ShotConditions(
            center_direction=center_direction,
            tilt_angle=tilt_angle,
        )

        # Generate student version (no planets)
        print(f"  - Generating student.pdf...")
        student_config = get_student_config(time)

        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=student_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=const_folder / "student.pdf",
        )

        # Generate student version with planets
        print(f"  - Generating student_with_planets.pdf...")
        student_planets_config = get_student_with_planets_config(time)

        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=student_planets_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=const_folder / "student_with_planets.pdf",
        )

        # Generate teacher version with all annotations
        print(f"  - Generating teacher.pdf...")
        constellation_teacher_config = get_teacher_config(time)

        # Create constellation config for teacher mode
        constellation_config = ConstellationConfig(
            constellations_list=None,  # Show all constellations
            constellation_color='gray',
            constellation_linewidth=0.5,
            constellation_alpha=0.5,
        )

        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=constellation_teacher_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=const_folder / "teacher.pdf",
            constellation_config=constellation_config,
        )

    print(
        f"\nCompleted! Generated samples for {len(constellations)} constellations.")
    print(f"Output directory: {root}")


def generate_random_sky_samples(
        output_folder: str,
        num_samples: int,
        time_interval: tuple[datetime, datetime],
        fov_deg: float = 90.0,
        max_magnitude: float = 6.0,
):
    """Generate sample PDFs for random sky areas.
    
    Each sample gets a folder with three PDFs:
    1. student.pdf - basic view without annotations
    2. student_with_planets.pdf - view with planets
    3. teacher.pdf - full view with all annotations and constellations

    :param output_folder: Root folder for output
    :param num_samples: Number of random samples to generate
    :param time_interval: Tuple of (start_time, end_time) for random time selection
    :param fov_deg: Field of view in degrees
    :param max_magnitude: Maximum star magnitude to display
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str:
    :param num_samples: int:
    :param time_interval: tuple[datetime:
    :param datetime: param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)
    :param output_folder: str: 
    :param num_samples: int: 
    :param time_interval: tuple[datetime: 
    :param datetime]: 
    :param fov_deg: float:  (Default value = 90.0)
    :param max_magnitude: float:  (Default value = 6.0)

    """
    # Setup
    root = Path(output_folder) / "random_sky"
    root.mkdir(parents=True, exist_ok=True)

    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=True)
    planet_catalog = PlanetCatalog()
    constraints = CatalogConstraints(max_magnitude=max_magnitude)

    # Camera configuration
    camera_cfg = CameraConfig.from_fov_and_aspect(
        fov_deg=fov_deg,
        aspect_ratio=1.5,
        height_pix=1000
    )

    start_time, end_time = time_interval
    time_delta = end_time - start_time

    print(f"Generating {num_samples} random sky area samples...")

    for i in range(num_samples):
        print(f"[{i + 1}/{num_samples}] Processing random area {i + 1:03d}...")

        # Create sample folder
        sample_folder = root / f"random_area_{i + 1:03d}"
        sample_folder.mkdir(exist_ok=True)

        # Random time
        random_seconds = random.uniform(0, time_delta.total_seconds())
        obs_time = start_time + timedelta(seconds=random_seconds)

        # Random direction in sky
        random_direction = generate_random_direction()

        # Random tilt angle
        random_tilt = random.uniform(-45, 45)

        shot_cond = ShotConditions(
            center_direction=random_direction,
            tilt_angle=random_tilt,
        )

        # Generate student version (no planets)
        print(f"  - Generating student.pdf...")
        student_config = get_student_config(obs_time)
        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=student_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=sample_folder / "student.pdf",
        )

        # Generate student version with planets
        print(f"  - Generating student_with_planets.pdf...")
        student_planets_config = get_student_with_planets_config(obs_time)
        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=student_planets_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=sample_folder / "student_with_planets.pdf",
        )

        # Generate teacher version with all annotations
        print(f"  - Generating teacher.pdf...")
        teacher_config = get_teacher_config(obs_time)

        # Create constellation config for teacher mode
        constellation_config = ConstellationConfig(
            constellations_list=None,  # Show all constellations
            constellation_color='gray',
            constellation_linewidth=0.8,
            constellation_alpha=0.6,
        )

        render_and_save(
            shot_cond=shot_cond,
            camera_cfg=camera_cfg,
            config=teacher_config,
            catalog=catalog,
            planet_catalog=planet_catalog,
            constraints=constraints,
            output_path=sample_folder / "teacher.pdf",
            constellation_config=constellation_config,
        )

    print(f"\nCompleted! Generated {num_samples} random sky area samples.")
    print(f"Output directory: {root}")


if __name__ == '__main__':
    # Example usage
    observation_time = datetime(2024, 6, 21, 22, 0,
                                0)  # Summer solstice evening

    # Generate samples for all constellations
    print("=" * 70)
    print("GENERATING CONSTELLATION SAMPLES")
    print("=" * 70)
    generate_constellation_samples(
        output_folder='pinhole_samples',
        time=observation_time,
        fov_deg=90.0,
        tilt_angle=0.0,
        max_magnitude=5.5,
    )

    # Generate random sky area samples
    print("\n" + "=" * 70)
    print("GENERATING RANDOM SKY AREA SAMPLES")
    print("=" * 70)
    start_time = datetime(2004, 1, 1, 0, 0, 0)
    end_time = datetime(2034, 12, 31, 23, 59, 59)

    generate_random_sky_samples(
        output_folder='pinhole_samples',
        num_samples=10,
        time_interval=(start_time, end_time),
        fov_deg=90.0,
        max_magnitude=5.5,
    )

    print("\n" + "=" * 70)
    print("ALL SAMPLES GENERATED SUCCESSFULLY!")
    print("=" * 70)