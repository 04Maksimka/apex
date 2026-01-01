"""Module for rendering constellation contours in pinhole projection.

This module extends the Pinhole projector to support drawing constellation
line patterns by connecting projected stars with their HIP catalog IDs.
"""
import numpy as np
from numpy.typing import NDArray
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from constellations_metadata.constellation_lines import get_constellation_lines
from pinhole_projection.pinhole_projector import Pinhole, ProjectionResult
from constellations_metadata.contellations_centers import Constellation


@dataclass
class ConstellationLineSegment:
    """Represents a projected line segment of a constellation."""
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
    
    def __init__(self, pinhole: Pinhole):
        """
        Initialize constellation renderer.
        
        Args:
            pinhole: Pinhole projector instance
        """
        self.pinhole = pinhole
        self._star_positions_cache: Optional[Dict[int, Tuple[float, float]]] = None
    
    def _build_star_positions_cache(self, stars: NDArray) -> Dict[int, Tuple[float, float]]:
        """
        Build a lookup dictionary from HIP ID to pixel coordinates.
        
        Args:
            stars: Structured array of projected stars
            
        Returns:
            Dictionary mapping HIP_ID to (x_pix, y_pix) tuples
        """
        cache = {}
        for star in stars:
            hip_id = int(star['hip_id'])
            x_pix = float(star['x_pix'])
            y_pix = float(star['y_pix'])
            cache[hip_id] = (x_pix, y_pix)
        return cache
    
    def get_constellation_segments(
        self, 
        constellation: Constellation,
        stars: Optional[NDArray] = None
    ) -> List[ConstellationLineSegment]:
        """
        Get projected line segments for a constellation.
        
        Args:
            constellation: The constellation to render
            stars: Optional pre-computed star projections. If None, will compute.
            
        Returns:
            List of ConstellationLineSegment objects representing visible lines
        """
        # Get constellation line data
        lines = get_constellation_lines(constellation)
        if not lines:
            return []
        
        # Get or use provided star projections
        if stars is None:
            projection_result = self.pinhole.project()
            stars = projection_result.stars
        
        # Build position cache if not already cached or if stars changed
        if self._star_positions_cache is None:
            self._star_positions_cache = self._build_star_positions_cache(stars)
        
        # Convert lines to segments
        segments = []
        for hip_id1, hip_id2 in lines:
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
        constellations: List[Constellation],
        stars: Optional[NDArray] = None
    ) -> Dict[Constellation, List[ConstellationLineSegment]]:
        """
        Get projected line segments for multiple constellations.
        
        Args:
            constellations: List of constellations to render
            stars: Optional pre-computed star projections
            
        Returns:
            Dictionary mapping each constellation to its line segments
        """
        # Get or compute star projections once
        if stars is None:
            projection_result = self.pinhole.project()
            stars = projection_result.stars
        
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
    ax,
    segments: List[ConstellationLineSegment],
    color: str = 'cyan',
    linewidth: float = 0.8,
    alpha: float = 0.7,
    linestyle: str = '-'
):
    """
    Draw constellation line segments on a matplotlib axis.
    
    Args:
        ax: Matplotlib axis object
        segments: List of ConstellationLineSegment objects
        color: Line color
        linewidth: Line width
        alpha: Line transparency (0-1)
        linestyle: Line style ('-', '--', '-.', ':')
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


def draw_multiple_constellations(
    ax,
    constellation_segments: Dict[Constellation, List[ConstellationLineSegment]],
    color: str = 'cyan',
    linewidth: float = 0.8,
    alpha: float = 0.7,
    linestyle: str = '-',
    color_map: Optional[Dict[Constellation, str]] = None
):
    """
    Draw multiple constellation line patterns on a matplotlib axis.
    
    Args:
        ax: Matplotlib axis object
        constellation_segments: Dictionary of constellation segments
        color: Default line color
        linewidth: Line width
        alpha: Line transparency
        linestyle: Line style
        color_map: Optional dictionary mapping constellations to specific colors
    """
    for constellation, segments in constellation_segments.items():
        line_color = color
        if color_map and constellation in color_map:
            line_color = color_map[constellation]
        
        draw_constellation_lines(
            ax, segments,
            color=line_color,
            linewidth=linewidth,
            alpha=alpha,
            linestyle=linestyle
        )
