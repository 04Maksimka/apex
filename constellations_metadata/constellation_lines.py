"""Module containing constellation line data.

This module stores the lines that connect stars to form constellation patterns.
Lines are stored as pairs of HIP (Hipparcos) catalog IDs.
"""
from enum import Enum
from typing import Dict, List, Tuple
from constellations_metadata.contellations_centers import Constellation

# Type alias for constellation lines: List of (HIP_ID1, HIP_ID2) pairs
ConstellationLines = List[Tuple[int, int]]

# Constellation line data - connections between stars by HIP ID
CONSTELLATION_LINES: Dict[Constellation, ConstellationLines] = {
    # Ursa Major (Большая Медведица) - Big Dipper
    Constellation.UMA: [
        (54061, 53910),  # Dubhe to Merak
        (53910, 58001),  # Merak to Phecda
        (58001, 59774),  # Phecda to Megrez
        (59774, 62956),  # Megrez to Alioth
        (62956, 65378),  # Alioth to Mizar
        (65378, 67301),  # Mizar to Alkaid
        (59774, 54061),  # Megrez to Dubhe (bowl connection)
    ],

    # Ursa Minor (Малая Медведица) - Little Dipper
    Constellation.UMI: [
        (11767, 77055),  # Polaris to Yildun
        (77055, 75097),  # Yildun to Epsilon UMi
        (75097, 72607),  # Epsilon to Zeta UMi
        (72607, 71075),  # Zeta to Eta UMi
        (71075, 79822),  # Eta to Gamma UMi
        (79822, 82080),  # Gamma to Beta UMi
        (82080, 11767),  # Beta to Polaris
    ],

    # Orion (Орион)
    Constellation.ORI: [
        (25336, 25930),  # Betelgeuse to Bellatrix
        (25930, 26311),  # Bellatrix to Alnitak
        (26311, 26727),  # Alnitak to Alnilam
        (26727, 26549),  # Alnilam to Mintaka
        (26727, 27989),  # Alnilam to Saiph
        (27989, 24436),  # Saiph to Rigel
        (24436, 26549),  # Rigel to Mintaka
        (26311, 25336),  # Alnitak to Betelgeuse
    ],

    # Cassiopeia (Кассиопея) - W shape
    Constellation.CAS: [
        (3179, 746),  # Caph to Schedar
        (746, 4427),  # Schedar to Gamma Cas
        (4427, 6686),  # Gamma to Ruchbah
        (6686, 8886),  # Ruchbah to Segin
    ],

    # Cygnus (Лебедь) - Northern Cross
    Constellation.CYG: [
        (102098, 100453),  # Deneb to Sadr
        (100453, 95947),  # Sadr to Gienah
        (100453, 104732),  # Sadr to Delta Cyg
        (104732, 97165),  # Delta to Albireo
        (100453, 102488),  # Sadr to Epsilon Cyg (crossbeam)
    ],

    # Leo (Лев)
    Constellation.LEO: [
        (49669, 50583),  # Regulus to Eta Leo
        (50583, 50335),  # Eta to Algieba
        (50335, 49583),  # Algieba to Adhafera
        (49583, 47908),  # Adhafera to Rasalas
        (49669, 54872),  # Regulus to Denebola
        (54872, 57632),  # Denebola to Zosma
        (57632, 50583),  # Zosma to Eta Leo
        (57632, 54879),  # Zosma to Chertan
    ],

    # Gemini (Близнецы)
    Constellation.GEM: [
        (36850, 37826),  # Castor to Pollux
        (36850, 34088),  # Castor to Alhena
        (37826, 35550),  # Pollux to Wasat
        (35550, 34088),  # Wasat to Alhena
        (36850, 30343),  # Castor to Mebsuta
        (37826, 36962),  # Pollux to Tejat
    ],

    # Taurus (Телец)
    Constellation.TAU: [
        (21421, 20889),  # Aldebaran to Epsilon Tau
        (20889, 20894),  # Epsilon to Delta Tau
        (20894, 21881),  # Delta to Theta2 Tau
        (21881, 20205),  # Theta2 to Gamma Tau
        (20205, 21421),  # Gamma to Aldebaran
        (21421, 25428),  # Aldebaran to Elnath
    ],

    # Aquila (Орёл)
    Constellation.AQL: [
        (97649, 93747),  # Altair to Tarazed
        (93747, 95501),  # Tarazed to Deneb el Okab
        (97649, 98036),  # Altair to Alshain
        (97649, 93805),  # Altair to Delta Aql
    ],

    # Lyra (Лира)
    Constellation.LYR: [
        (91262, 91919),  # Vega to Epsilon Lyr
        (91262, 91926),  # Vega to Zeta Lyr
        (91926, 92791),  # Zeta to Beta Lyr
        (92791, 93194),  # Beta to Gamma Lyr
    ],

    # Scorpius (Скорпион)
    Constellation.SCO: [
        (80763, 78820),  # Antares to Tau Sco
        (78820, 78265),  # Tau to Epsilon Sco
        (78265, 79593),  # Epsilon to Delta Sco
        (79593, 81266),  # Delta to Beta Sco
        (80763, 80112),  # Antares to Sigma Sco
        (80112, 85927),  # Sigma to Lambda Sco
        (85927, 86228),  # Lambda to Shaula
        (86228, 85696),  # Shaula to Lesath
    ],

    # Sagittarius (Стрелец) - Teapot
    Constellation.SGR: [
        (88635, 90185),  # Kaus Australis to Kaus Media
        (90185, 89931),  # Kaus Media to Kaus Borealis
        (89931, 92855),  # Kaus Borealis to Nunki
        (92855, 93506),  # Nunki to Tau Sgr
        (93506, 95241),  # Tau to Phi Sgr
        (95241, 88635),  # Phi to Kaus Australis (complete teapot body)
        (90185, 93864),  # Kaus Media to Ascella (handle)
    ],

    # Andromeda (Андромеда)
    Constellation.AND: [
        (677, 3092),  # Alpheratz to Mirach
        (3092, 5447),  # Mirach to Almach
        (3092, 9640),  # Mirach to Delta And
        (9640, 7607),  # Delta to Beta And
    ],

    # Perseus (Персей)
    Constellation.PER: [
        (15863, 14328),  # Mirfak to Gamma Per
        (14328, 13268),  # Gamma to Delta Per
        (13268, 14576),  # Delta to Epsilon Per
        (14576, 15863),  # Epsilon to Mirfak
        (13847, 14328),  # Algol to Gamma Per
    ],

    # Pegasus (Пегас) - Great Square
    Constellation.PEG: [
        (677, 113881),  # Alpheratz to Scheat
        (113881, 113963),  # Scheat to Markab
        (113963, 112158),  # Markab to Algenib
        (112158, 677),  # Algenib to Alpheratz
        (113963, 107315),  # Markab to Enif
    ],

    # Aquarius (Водолей)
    Constellation.AQR: [
        (110960, 109074),  # Sadalsuud to Sadalmelik
        (109074, 106278),  # Sadalmelik to Lambda Aqr
        (110960, 111123),  # Sadalsuud to Xi Aqr
        (111123, 112961),  # Xi to Theta Aqr
        (112961, 113136),  # Theta to Delta Aqr
    ],

    # Capricornus (Козерог)
    Constellation.CAP: [
        (100345, 100064),  # Prima Giedi to Secunda Giedi
        (100064, 102978),  # Secunda to Dabih
        (102978, 105881),  # Dabih to Nashira
        (105881, 107556),  # Nashira to Deneb Algedi
        (107556, 106985),  # Deneb to Omega Cap
    ],

    # Aries (Овен)
    Constellation.ARI: [
        (8903, 9884),  # Hamal to Sheratan
        (9884, 8832),  # Sheratan to Mesarthim
        (8903, 13209),  # Hamal to 41 Ari
    ],

    # Cancer (Рак)
    Constellation.CNC: [
        (42911, 43103),  # Acubens to Asellus Borealis
        (43103, 42806),  # Asellus Borealis to Asellus Australis
        (42806, 40526),  # Asellus Australis to Beta Cnc
    ],

    # Virgo (Дева)
    Constellation.VIR: [
        (65474, 63608),  # Spica to Porrima
        (63608, 60129),  # Porrima to Vindemiatrix
        (60129, 57757),  # Vindemiatrix to Delta Vir
        (57757, 63090),  # Delta to Zavijava
        (63090, 65474),  # Zavijava to Spica
    ],

    # Libra (Весы)
    Constellation.LIB: [
        (74785, 72622),  # Zubenelgenubi to Zubeneschamali
        (72622, 76333),  # Zubeneschamali to Sigma Lib
        (76333, 74785),  # Sigma to Zubenelgenubi
    ],

    # Draco (Дракон)
    Constellation.DRA: [
        (87833, 85670),  # Thuban to Edasich
        (85670, 83895),  # Edasich to Aldhibah
        (83895, 80331),  # Aldhibah to Altais
        (80331, 78527),  # Altais to Chi Dra
        (78527, 75458),  # Chi to Grumium
        (75458, 68756),  # Grumium to Eltanin
        (68756, 61281),  # Eltanin to Rastaban
        (61281, 56211),  # Rastaban to Kuma
    ],

    # Auriga (Возничий)
    Constellation.AUR: [
        (24608, 25428),  # Capella to Menkalinan
        (25428, 28360),  # Menkalinan to Theta Aur
        (28360, 23015),  # Theta to Hassaleh
        (23015, 24608),  # Hassaleh to Capella
        (24608, 28380),  # Capella to Epsilon Aur
    ],

    # Bootes (Волопас)
    Constellation.BOO: [
        (69673, 71075),  # Arcturus to Muphrid
        (69673, 67927),  # Arcturus to Seginus
        (67927, 69483),  # Seginis to Izar
        (69483, 69673),  # Izar to Arcturus
        (71075, 72105),  # Muphrid to Nekkar
    ],

    # Cepheus (Цефей)
    Constellation.CEP: [
        (105199, 106032),  # Alderamin to Alfirk
        (106032, 108917),  # Alfirk to Errai
        (108917, 109857),  # Errai to Alrai
        (109857, 116727),  # Alrai to Erakis
        (116727, 105199),  # Erakis to Alderamin
    ],

    # Hercules (Геркулес)
    Constellation.HER: [
        (84345, 85693),  # Rasalgethi to Kornephoros
        (85693, 81693),  # Kornephoros to Zeta Her
        (81693, 80816),  # Zeta to Pi Her
        (80816, 84345),  # Pi to Rasalgethi
        (85693, 86974),  # Kornephoros to Sarin
        (86974, 87808),  # Sarin to Eta Her
    ],
}


def get_constellation_lines(constellation: Constellation) -> ConstellationLines:
    """
    Get the line segments for a constellation.

    Args:
        constellation: The constellation enum

    Returns:
        List of tuples (HIP_ID1, HIP_ID2) representing line segments
    """
    return CONSTELLATION_LINES.get(constellation, [])


def get_available_constellations() -> List[Constellation]:
    """
    Get list of constellations that have line data available.

    Returns:
        List of Constellation enums with line data
    """
    return list(CONSTELLATION_LINES.keys())