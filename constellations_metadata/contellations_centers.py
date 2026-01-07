"""Constellation centers and helper functions for constellation navigation.

This module provides an Enum of constellation abbreviations and helper functions
to get constellation direction vectors in ECI (Earth-Centered Inertial) coordinates.
"""
from enum import Enum
import numpy as np
from typing import Optional

from constellations_metadata.constellations_data import (
    get_constellation_center,
    get_available_constellations
)


class Constellation(Enum):
    """Enumeration of constellation abbreviations."""
    AND = "AND"  # Andromeda
    ANT = "ANT"  # Antlia
    APS = "APS"  # Apus
    AQR = "AQR"  # Aquarius
    AQL = "AQL"  # Aquila
    ARA = "ARA"  # Ara
    ARI = "ARI"  # Aries
    AUR = "AUR"  # Auriga
    BOO = "BOO"  # Boötes
    CAE = "CAE"  # Caelum
    CAM = "CAM"  # Camelopardalis
    CNC = "CNC"  # Cancer
    CVN = "CVN"  # Canes Venatici
    CMA = "CMA"  # Canis Major
    CMI = "CMI"  # Canis Minor
    CAP = "CAP"  # Capricornus
    CAR = "CAR"  # Carina
    CAS = "CAS"  # Cassiopeia
    CEN = "CEN"  # Centaurus
    CEP = "CEP"  # Cepheus
    CET = "CET"  # Cetus
    CHA = "CHA"  # Chamaeleon
    CIR = "CIR"  # Circinus
    COL = "COL"  # Columba
    COM = "COM"  # Coma Berenices
    CRA = "CRA"  # Corona Australis
    CRB = "CRB"  # Corona Borealis
    CRV = "CRV"  # Corvus
    CRT = "CRT"  # Crater
    CRU = "CRU"  # Crux
    CYG = "CYG"  # Cygnus
    DEL = "DEL"  # Delphinus
    DOR = "DOR"  # Dorado
    DRA = "DRA"  # Draco
    EQU = "EQU"  # Equuleus
    ERI = "ERI"  # Eridanus
    FOR = "FOR"  # Fornax
    GEM = "GEM"  # Gemini
    GRU = "GRU"  # Grus
    HER = "HER"  # Hercules
    HOR = "HOR"  # Horologium
    HYA = "HYA"  # Hydra
    HYI = "HYI"  # Hydrus
    IND = "IND"  # Indus
    LAC = "LAC"  # Lacerta
    LEO = "LEO"  # Leo
    LMI = "LMI"  # Leo Minor
    LEP = "LEP"  # Lepus
    LIB = "LIB"  # Libra
    LUP = "LUP"  # Lupus
    LYN = "LYN"  # Lynx
    LYR = "LYR"  # Lyra
    MEN = "MEN"  # Mensa
    MIC = "MIC"  # Microscopium
    MON = "MON"  # Monoceros
    MUS = "MUS"  # Musca
    NOR = "NOR"  # Norma
    OCT = "OCT"  # Octans
    OPH = "OPH"  # Ophiuchus
    ORI = "ORI"  # Orion
    PAV = "PAV"  # Pavo
    PEG = "PEG"  # Pegasus
    PER = "PER"  # Perseus
    PHE = "PHE"  # Phoenix
    PIC = "PIC"  # Pictor
    PSC = "PSC"  # Pisces
    PSA = "PSA"  # Piscis Austrinus
    PUP = "PUP"  # Puppis
    PYX = "PYX"  # Pyxis
    RET = "RET"  # Reticulum
    SGE = "SGE"  # Sagitta
    SGR = "SGR"  # Sagittarius
    SCO = "SCO"  # Scorpius
    SCL = "SCL"  # Sculptor
    SCT = "SCT"  # Scutum
    SER = "SER"  # Serpens
    SEX = "SEX"  # Sextans
    TAU = "TAU"  # Taurus
    TEL = "TEL"  # Telescopium
    TRI = "TRI"  # Triangulum
    TRA = "TRA"  # Triangulum Australe
    TUC = "TUC"  # Tucana
    UMA = "UMA"  # Ursa Major
    UMI = "UMI"  # Ursa Minor
    VEL = "VEL"  # Vela
    VIR = "VIR"  # Virgo
    VOL = "VOL"  # Volans
    VUL = "VUL"  # Vulpecula


def get_constellation_dir(constellation: Constellation) -> np.ndarray:
    """Get the direction vector (unit vector in ECI) pointing to constellation center.
    
    Args:
        constellation: Constellation enum value
        
    Returns:
        numpy array: Unit vector [x, y, z] in ECI coordinates pointing to constellation center
        
    Raises:
        ValueError: If constellation center is not found in data
    """
    center = get_constellation_center(constellation.value)
    
    if center is None:
        raise ValueError(f"Constellation center not found for {constellation.value}")
    
    center_array = np.array(center, dtype=float)
    
    # Normalize to ensure it's a unit vector
    norm = np.linalg.norm(center_array)
    if norm == 0:
        raise ValueError(f"Invalid constellation center (zero vector) for {constellation.value}")
    
    return center_array / norm


def get_constellation_by_abbr(abbr: str) -> Optional[Constellation]:
    """Get Constellation enum from abbreviation string.
    
    Args:
        abbr: Three-letter constellation abbreviation (e.g., "GEM", "UMA")
        
    Returns:
        Constellation enum value or None if not found
    """
    try:
        return Constellation(abbr.upper())
    except ValueError:
        return None


def list_all_constellations() -> list[Constellation]:
    """Get a list of all available constellations.
    
    Returns:
        List of all Constellation enum values
    """
    return list(Constellation)
