"""Module with planets catalog."""
from dataclasses import dataclass
from enum import IntEnum


class Planets(IntEnum):
    """Planets of the Solar system."""

@dataclass
class PlanetCatalog(object):
    """Planets Catalog."""
