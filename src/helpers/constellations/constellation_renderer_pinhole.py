"""Module for rendering constellation contours in pinhole projection.

This module extends the Pinhole projector to support drawing constellation
line patterns by connecting projected stars with their HIP catalog IDs.
"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from numpy.typing import NDArray
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from src.constellations_metadata.constellations_data import get_constellation_name, get_constellation_lines
from src.hip_catalog.hip_catalog import CatalogConstraints


@dataclass
class ConstellationLineSegment:
    """ Represents a projected line segment of a constellation. """

    x1: float  # Start point X coordinate in pixels
    y1: float  # Start point Y coordinate in pixels
    x2: float  # End point X coordinate in pixels
    y2: float  # End point Y coordinate in pixels
    hip_id1: int  # HIP ID of first star
    hip_id2: int  # HIP ID of second star

    def to_array(self) -> NDArray:
        """Convert line segment to numpy array for plotting."""
        return np.array([[self.x1, self.y1], [self.x2, self.y2]])


class ConstellationRenderer:
    """Renderer for constellation line patterns in pinhole projection."""

    def __init__(self):
        """ Initialize constellation renderer.  """

        self._star_positions_cache: Optional[
            Dict[int, Tuple[float, float]]] = None


    @staticmethod
    def _build_star_positions_cache(stars: NDArray) -> Dict[int, Tuple[float, float]]:
        """Build a lookup dictionary from HIP ID to pixel coordinates.

        :param stars: Structured array of projected stars
        :type stars: NDArray:

        :return: Dictionary mapping HIP_ID to (x_pix, y_pix) tuples
        :rtype: Dict[int, Tuple[float, float]]
        """

        cache = {}
        for star in stars:
            hip_id = int(star['id'])
            x_pix = float(star['x_pix'])
            y_pix = float(star['y_pix'])
            cache[hip_id] = (x_pix, y_pix)
        return cache

    def get_constellation_segments(
            self,
            constellation: str,
            stars: Optional[NDArray] = None,
            constraints: CatalogConstraints = None
    ) -> List[ConstellationLineSegment]:
        """Get projected line segments for a constellation.

        :param constraints: param constellation: The constellation to render
        :type stars: Optional[NDArray]:  (Default value = None)
        :param stars: pre-computed star projections. If None, will compute.
        :type constraints: CatalogConstraints:  (Default value = None)
        :param constellation: constellation name
        :type constellation: str

        :return: List of ConstellationLineSegment objects representing visible lines
        :rtype: List[ConstellationLineSegment]
        """

        # Get constellation line data
        lines = get_constellation_lines(constellation)
        if not lines:
            return []

        # Build position cache if not already cached or if stars changed
        if self._star_positions_cache is None:
            self._star_positions_cache = self._build_star_positions_cache(stars)

        # Convert lines to segments
        segments = []
        for line in lines:
            for idx1 in range(len(line) - 1):
                idx2 = idx1 + 1
                hip_id1 = line[idx1]
                hip_id2 = line[idx2]
                # Check if both stars are visible in the projection
                if hip_id1 in self._star_positions_cache and hip_id2 in self._star_positions_cache:
                    x1, y1 = self._star_positions_cache[hip_id1]
                    x2, y2 = self._star_positions_cache[hip_id2]

                    segment = ConstellationLineSegment(
                        x1=x1, y1=y1,
                        x2=x2, y2=y2,
                        hip_id1=hip_id1,
                        hip_id2=hip_id2
                    )
                    segments.append(segment)

        return segments

    def get_multiple_constellation_segments(
            self,
            constellations: List[str],
            stars: Optional[NDArray] = None,
    ) -> Dict[str, List[ConstellationLineSegment]]:
        """Get projected line segments for multiple constellations.

        :param constellations: List of constellations to render
        :type constellations: List[str]
        :param stars: Optional pre-computed star projections
        :type stars: Optional[NDArray]:  (Default value = None)

        :return: Dictionary mapping each constellation to its line segments
        :rtype: Dict[str, List[ConstellationLineSegment]]
        """

        # Build cache once for all constellations
        self._star_positions_cache = self._build_star_positions_cache(stars)

        # Get segments for each constellation
        result = {}
        for constellation in constellations:
            segments = self.get_constellation_segments(constellation, stars)
            if segments:  # Only include constellations with visible segments
                result[constellation] = segments

        return result

    def clear_cache(self):
        """Clear the internal star position cache."""

        self._star_positions_cache = None


def draw_constellation_lines(
        ax: plt.Axes,
        segments: List[ConstellationLineSegment],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-'
):
    """Draw constellation line segments on a matplotlib axis.
    
    This function correctly handles coordinate systems. If you use ax.invert_xaxis()
    in your plotting code (common for astronomical visualizations), the lines will
    automatically adapt to the inverted coordinates.

    :param ax: Matplotlib axis object
    :type ax: plt.Axes
    :param segments: Constellation segments to connect and show on map
    :type segments: List[ConstellationLineSegment]:
    :param color: Line color
    :type color: str:  (Default value = 'cyan')
    :param linewidth: Line width
    :type linewidth: float:  (Default value = 0.8)
    :param alpha: Line transparency (0-1)
    :type alpha: float:  (Default value = 0.7)
    :param linestyle: Line style ('-', '--', '-.', ':')
    :type linestyle: str:  (Default value = '-')
    """

    for segment in segments:
        ax.plot(
            [segment.x1, segment.x2],
            [segment.y1, segment.y2],
            color=color,
            linewidth=linewidth,
            alpha=alpha,
            linestyle=linestyle,
            zorder=1  # Draw lines below stars
        )

def draw_constellation_lines_collection(
        ax: plt.Axes,
        segments: List[ConstellationLineSegment],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-'
) -> Optional[LineCollection]:
    """Draw constellation line segments using LineCollection for better performance.

    :param ax: Matplotlib axis object
    :type ax: plt.Axes
    :param segments: Constellations segments to connect and show on map
    :type segments: List[ConstellationLineSegment]:
    :param color: Line color
    :type color: str:  (Default value = 'cyan')
    :param linewidth: Line width
    :type linewidth: float:  (Default value = 0.8)
    :param alpha: Line transparency (0-1)
    :type alpha: float:  (Default value = 0.7)
    :param linestyle: Line style ('-', '--', '-.', ':')
    :type linestyle: str:  (Default value = '-')

    :return: Collection of constellations if there are any constellation to show
    :rtype: LineCollection | None
    """

    if not segments:
        return None

    # Convert segments to line collection format
    lines = []
    for segment in segments:
        lines.append(
            np.column_stack([
                [segment.x1, segment.x2],
                [segment.y1, segment.y2]
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
        ax: plt.Axes,
        constellation_segments: Dict[str, List[ConstellationLineSegment]],
        color: str = 'cyan',
        linewidth: float = 0.8,
        alpha: float = 0.7,
        linestyle: str = '-',
        color_map: Optional[Dict[str, str]] = None,
        use_collection: bool = False
) -> Dict:
    """Draw multiple constellation line patterns on a matplotlib axis.

    :param ax: Matplotlib axis object
    :type ax: plt.Axes
    :param constellation_segments: Dictionary of constellation segments
    :type constellation_segments: Dict[str, List[ConstellationLineSegment]]
    :param color: Default line color
    :type color: str:  (Default value = 'cyan')
    :param linewidth: Line width
    :type linewidth: float:  (Default value = 0.8)
    :param alpha: Line transparency
    :type alpha: float:  (Default value = 0.7)
    :param linestyle: Line style
    :type linestyle: str:  (Default value = '-')
    :param color_map: Optional dictionary mapping constellations to specific colors
    :param use_collection: flag for configuring rendering using LineCollection to draw constellations
    :type use_collection: bool:  (Default value = False)

    :return: Dictionary of constellation lines drawn on a matplotlib axis
    :rtype: Dict
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

