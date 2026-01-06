"""Module for rendering constellation contours in stereographic projection.

This module extends the StereoProjector to support drawing constellation
line patterns by connecting projected stars with their HIP catalog IDs.
"""
import numpy as np
from numpy.typing import NDArray
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from matplotlib.collections import LineCollection

from constellations_metadata.constellations_data import get_constellation_lines, get_constellation_name


@dataclass
class ConstellationLineSegmentPolar:
    """Represents a projected line segment of a constellation in polar coordinates."""

    angle1: float   # Start point angle (azimuth) in radians
    radius1: float  # Start point radius (from center)
    angle2: float   # End point angle in radians
    radius2: float  # End point radius
    hip_id1: int    # HIP ID of first star
    hip_id2: int    # HIP ID of second star

    def to_array(self) -> NDArray:
        """Convert line segment to numpy array for polar plotting."""
        return np.array(
            [[self.angle1, self.radius1], [self.angle2, self.radius2]])


class ConstellationRendererStereo:
    """Renderer for constellation line patterns in stereographic projection."""

    def __init__(self):
        """Initialize constellation renderer for stereographic projection."""
        self._star_positions_cache: Optional[
            Dict[int, Tuple[float, float]]] = None

    def _build_star_positions_cache(self, projection_data: NDArray) -> Dict[
        int, Tuple[float, float]]:
        """
        Build a lookup dictionary from HIP ID to polar coordinates.

        :param projection_data: Structured array of projected stars with 'angle', 'radius', 'id'
        :return: Dictionary mapping HIP_ID to (angle, radius) tuples
        """

        cache = {}
        for star in projection_data:
            hip_id = int(star['id'])  # 'id' field contains HIP ID
            angle = float(star['angle'])
            radius = float(star['radius'])
            cache[hip_id] = (angle, radius)
        return cache

    def get_constellation_segments(
            self,
            constellation: str,
            projection_data: NDArray
    ) -> List[ConstellationLineSegmentPolar]:
        """
        Get projected line segments for a constellation in polar coordinates.

        :param constellation: The constellation to render
        :param projection_data: Projected star data with 'angle', 'radius', 'id' fields
        :return: List of ConstellationLineSegmentPolar objects representing visible lines
        """

        # Get constellation line data
        lines = get_constellation_lines(constellation)
        if not lines:
            return []

        # Build position cache
        if self._star_positions_cache is None:
            self._star_positions_cache = self._build_star_positions_cache(
                projection_data)

        # Convert lines to segments
        segments = []
        for line in lines:
            for idx1 in range(len(line) - 1):
                idx2 = idx1 + 1
                hip_id1 = line[idx1]
                hip_id2 = line[idx2]
                # Check if both stars are visible in the projection
                if hip_id1 in self._star_positions_cache and hip_id2 in self._star_positions_cache:
                    angle1, radius1 = self._star_positions_cache[hip_id1]
                    angle2, radius2 = self._star_positions_cache[hip_id2]

                    segment = ConstellationLineSegmentPolar(
                        angle1=angle1, radius1=radius1,
                        angle2=angle2, radius2=radius2,
                        hip_id1=hip_id1,
                        hip_id2=hip_id2
                    )
                    segments.append(segment)

        return segments

    def get_multiple_constellation_segments(
            self,
            constellations: List[str],
            projection_data: NDArray
    ) -> Dict[str, List[ConstellationLineSegmentPolar]]:
        """
        Get projected line segments for multiple constellations.

        :param constellations: List of constellations to render
        :param projection_data: Projected star data

        :return: Dictionary mapping each constellation to its line segments
        """
        # Build cache once for all constellations
        self._star_positions_cache = self._build_star_positions_cache(
            projection_data)

        # Get segments for each constellation
        result = {}
        for constellation in constellations:
            segments = self.get_constellation_segments(constellation,
                                                       projection_data)
            if segments:  # Only include constellations with visible segments
                result[constellation] = segments

        return result

    def clear_cache(self):
        """Clear the internal star position cache."""
        self._star_positions_cache = None


def draw_constellation_lines(
        ax,
        segments: List[ConstellationLineSegmentPolar],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-'
):
    """
    Draw constellation line segments on a polar matplotlib axis.

    :param ax: Matplotlib polar axis object
    :param segments: List of ConstellationLineSegmentPolar objects
    :param color: Line color
    :param linewidth: Line width
    :param alpha: Line transparency (0-1)
    :param linestyle: Line style ('-', '--', '-.', ':')
    """
    for segment in segments:
        ax.plot(
            [segment.angle1, segment.angle2],
            [segment.radius1, segment.radius2],
            color=color,
            linewidth=linewidth,
            alpha=alpha,
            linestyle=linestyle,
            zorder=1  # Draw lines below stars
        )


def draw_constellation_lines_collection(
        ax,
        segments: List[ConstellationLineSegmentPolar],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-'
):
    """
    Draw constellation line segments using LineCollection for better performance.

    :param ax: Matplotlib polar axis object
    :param segments: List of ConstellationLineSegmentPolar objects
    :param color: Line color
    :param linewidth: Line width
    :param alpha: Line transparency (0-1)
    :param linestyle: Line style ('-', '--', '-.', ':')
    """
    if not segments:
        return

    # Convert segments to line collection format
    lines = []
    for segment in segments:
        lines.append(
            np.column_stack([
                [segment.angle1, segment.angle2],
                [segment.radius1, segment.radius2]
            ])
        )

    # Create and add line collection
    lc = LineCollection(
        lines,
        colors=color,
        linewidths=linewidth,
        alpha=alpha,
        linestyles=linestyle,
        zorder=0  # Draw lines below stars
    )
    ax.add_collection(lc)
    return lc


def draw_multiple_constellations(
        ax,
        constellation_segments: Dict[
            str, List[ConstellationLineSegmentPolar]],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-',
        color_map: Optional[Dict[str, str]] = None,
        use_collection: bool = True
) -> Dict:
    """
    Draw multiple constellation line patterns on a polar matplotlib axis.

    :param ax: Matplotlib polar axis object
    :param constellation_segments: Dictionary of constellation segments
    :param color: Default line color
    :param linewidth: Line width
    :param alpha: Line transparency
    :param linestyle: Line style
    :param color_map: Optional dictionary mapping constellations to specific colors
    :param use_collection: Use LineCollection for better performance (default True)
    :return: Dictionary mapping constellations to their line collection/plot objects
    """

    result = {}
    for constellation, segments in constellation_segments.items():
        line_color = color
        if color_map and constellation in color_map:
            line_color = color_map[constellation]

        if use_collection:
            lc = draw_constellation_lines_collection(
                ax, segments,
                color=line_color,
                linewidth=linewidth,
                alpha=alpha,
                linestyle=linestyle
            )
            result[constellation] = {'name': get_constellation_name(constellation), 'lc': lc}
        else:
            draw_constellation_lines(
                ax, segments,
                color=line_color,
                linewidth=linewidth,
                alpha=alpha,
                linestyle=linestyle
            )

    return result
