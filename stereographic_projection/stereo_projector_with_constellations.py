"""Extended stereographic projector with constellation support."""
from typing import Optional, List, Dict
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from stereographic_projection.stereographic_projector import (
    StereoProjector,
    StereoProjConfig
)
from hip_catalog.hip_catalog import Catalog, CatalogConstraints
from planets_catalog.planet_catalog import PlanetCatalog
from constellations_metadata.contellations_centers import Constellation
from constellation_renderer_stereo import (
    ConstellationRendererStereo,
    draw_multiple_constellations
)


@dataclass
class StereoConstellationConfig(StereoProjConfig):
    """Extended configuration with constellation support."""

    # Constellation flags
    add_constellations: bool = False
    constellations_list: Optional[
        List[Constellation]] = None  # If None, render all available
    constellation_color: str = 'cyan'
    constellation_linewidth: float = 0.8
    constellation_alpha: float = 0.7
    constellation_color_map: Optional[Dict[Constellation, str]] = None


class StereoProjectorWithConstellations(StereoProjector):
    """Stereographic projector with constellation line rendering support."""

    def __init__(
            self,
            config: StereoConstellationConfig,
            catalog: Catalog,
            planets_catalog: PlanetCatalog,
            random_angle: float = np.random.uniform(0.0, 2 * np.pi)
    ):
        """
        Initialize projector with constellation support.

        Args:
            config: Extended configuration with constellation settings
            catalog: Star catalog
            planets_catalog: Planet catalog
            random_angle: Random angle for orientation
        """
        super().__init__(config, catalog, planets_catalog, random_angle)
        self.constellation_renderer = ConstellationRendererStereo()
        self._projection_data: Optional[NDArray] = None

    def generate(self, constraints: Optional[CatalogConstraints] = None):
        """
        Generate a projection with optional constellations.

        Args:
            constraints: Catalog constraints for star filtering

        Returns:
            Matplotlib figure with the projection
        """
        # Get catalog
        _ = self.catalog.get_stars(constraints)

        # From equatorial to horizontal
        star_view_data = self._make_horizontal_views(
            data=self.catalog.data,
            object_type='star'
        )

        # Make projections
        from helpers.geometry import make_projections
        points_data = make_projections(
            view_data=star_view_data,
            constraints=self.catalog.constraints,
        )

        # Store for constellation rendering
        self._projection_data = points_data

        # Make figure with projections
        self._create_polar_scatter(points_data)

        # Add ecliptic
        if self.config.add_ecliptic:
            self._add_ecliptic()

        # Add equator
        if self.config.add_equator:
            self._add_equator()

        # Add galactic equator
        if self.config.add_galactic_equator:
            self._add_galactic_equator()

        # Add horizontal grid
        if self.config.add_horizontal_grid:
            self._add_horizontal_grid()

        # Add equatorial grid
        if self.config.add_equatorial_grid:
            self._add_equatorial_grid()

        # Add constellations (NEW FEATURE)
        if self.config.add_constellations:
            self._add_constellations()

        # Add planets
        if self.config.add_planets:
            from helpers.geometry import make_projections
            planet_data = self.planets_catalog.get_planets(
                self.config.local_time)
            planet_view_data = self._make_horizontal_views(
                data=planet_data,
                object_type='planet'
            )
            planet_points_data = make_projections(
                view_data=planet_view_data,
                constraints=self.catalog.constraints,
            )
            self._add_planets(planet_points_data)

        # Put a legend to the bottom of the current axis
        self._create_grouped_legend()

        return self._fig

    def _add_constellations(self):
        """Add constellation line patterns to the projection."""
        if self._projection_data is None:
            return

        # Determine which constellations to render
        from constellations_metadata.constellation_lines import \
            get_available_constellations

        if self.config.constellations_list is not None:
            constellations_to_render = self.config.constellations_list
        else:
            constellations_to_render = get_available_constellations()

        # Get constellation segments
        constellation_segments = self.constellation_renderer.get_multiple_constellation_segments(
            constellations=constellations_to_render,
            projection_data=self._projection_data
        )

        if not constellation_segments:
            return

        # Draw constellations
        lcs = draw_multiple_constellations(
            ax=self._ax,
            constellation_segments=constellation_segments,
            color=self.config.constellation_color,
            linewidth=self.config.constellation_linewidth,
            alpha=self.config.constellation_alpha,
            color_map=self.config.constellation_color_map,
            use_collection=True
        )

        # Add to legend groups
        if lcs:
            # Get first line collection for legend
            first_lc = next(iter(lcs.values()))
            self._groups['Constellations'] = self._groups.get('Constellations',
                                                              []) + [
                                                 (first_lc,
                                                  f'Constellations ({len(constellation_segments)})')
                                             ]