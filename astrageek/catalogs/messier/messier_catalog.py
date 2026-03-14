"""Catalog of Messier deep-sky objects.

The Messier catalog contains 110 deep-sky objects including galaxies,
nebulae, star clusters, and other astronomical objects compiled by
Charles Messier in the 18th century.
"""

from enum import IntEnum
from typing import Optional

import numpy as np
from numpy.typing import NDArray


class MessierType(IntEnum):
    """Types of Messier objects."""

    GALAXY = 1  # Galaxy
    GLOBULAR_CLUSTER = 2  # Globular star cluster
    OPEN_CLUSTER = 3  # Open star cluster
    NEBULA = 4  # Nebula (emission, reflection, or planetary)
    SUPERNOVA_REMNANT = 5  # Supernova remnant
    STAR_CLOUD = 6  # Star cloud
    DOUBLE_STAR = 7


class MessierCatalog:
    """
    Catalog of Messier deep-sky objects.
    Complete Messier catalog data
    Format:
    (M_number, name, RA_hours, RA_min, RA_sec, Dec_deg, Dec_min,
    Dec_sec, magnitude, size_arcmin, type, constellation)
    """

    MESSIER_DATA = [
        (
            1,
            "Crab Nebula",
            5,
            34,
            31.94,
            22,
            0,
            52.2,
            8.4,
            6.0,
            MessierType.SUPERNOVA_REMNANT,
            "Tau",
        ),
        (
            2,
            "",
            21,
            33,
            27.02,
            -0,
            49,
            23.7,
            6.3,
            16.0,
            MessierType.GLOBULAR_CLUSTER,
            "Aqr",
        ),
        (
            3,
            "",
            13,
            42,
            11.62,
            28,
            22,
            38.2,
            6.2,
            18.0,
            MessierType.GLOBULAR_CLUSTER,
            "CVn",
        ),
        (
            4,
            "",
            16,
            23,
            35.22,
            -26,
            31,
            32.7,
            5.9,
            36.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sco",
        ),
        (
            5,
            "",
            15,
            18,
            33.22,
            2,
            4,
            51.7,
            5.7,
            23.0,
            MessierType.GLOBULAR_CLUSTER,
            "Ser",
        ),
        (
            6,
            "Butterfly Cluster",
            17,
            40,
            20.0,
            -32,
            15,
            12.0,
            4.2,
            25.0,
            MessierType.OPEN_CLUSTER,
            "Sco",
        ),
        (
            7,
            "Ptolemy Cluster",
            17,
            53,
            51.0,
            -34,
            47,
            34.0,
            3.3,
            80.0,
            MessierType.OPEN_CLUSTER,
            "Sco",
        ),
        (
            8,
            "Lagoon Nebula",
            18,
            3,
            37.0,
            -24,
            23,
            12.0,
            5.8,
            90.0,
            MessierType.NEBULA,
            "Sgr",
        ),
        (
            9,
            "",
            17,
            19,
            11.78,
            -18,
            30,
            58.5,
            7.7,
            12.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            10,
            "",
            16,
            57,
            8.92,
            -4,
            5,
            58.0,
            6.4,
            20.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            11,
            "Wild Duck Cluster",
            18,
            51,
            5.0,
            -6,
            16,
            0.0,
            5.8,
            14.0,
            MessierType.OPEN_CLUSTER,
            "Sct",
        ),
        (
            12,
            "",
            16,
            47,
            14.18,
            -1,
            56,
            54.7,
            6.1,
            16.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            13,
            "Great Hercules Cluster",
            16,
            41,
            41.24,
            36,
            27,
            35.5,
            5.8,
            20.0,
            MessierType.GLOBULAR_CLUSTER,
            "Her",
        ),
        (
            14,
            "",
            17,
            37,
            36.15,
            -3,
            14,
            45.3,
            7.6,
            11.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            15,
            "",
            21,
            29,
            58.33,
            12,
            10,
            1.2,
            6.2,
            18.0,
            MessierType.GLOBULAR_CLUSTER,
            "Peg",
        ),
        (
            16,
            "Eagle Nebula",
            18,
            18,
            48.0,
            -13,
            48,
            24.0,
            6.0,
            7.0,
            MessierType.NEBULA,
            "Ser",
        ),
        (
            17,
            "Omega/Swan Nebula",
            18,
            20,
            26.0,
            -16,
            10,
            36.0,
            6.0,
            11.0,
            MessierType.NEBULA,
            "Sgr",
        ),
        (
            18,
            "",
            18,
            19,
            58.0,
            -17,
            6,
            7.0,
            6.9,
            9.0,
            MessierType.OPEN_CLUSTER,
            "Sgr",
        ),
        (
            19,
            "",
            17,
            2,
            37.69,
            -26,
            16,
            4.6,
            6.8,
            17.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            20,
            "Trifid Nebula",
            18,
            2,
            23.0,
            -22,
            58,
            18.0,
            6.3,
            28.0,
            MessierType.NEBULA,
            "Sgr",
        ),
        (
            21,
            "",
            18,
            4,
            13.0,
            -22,
            29,
            24.0,
            5.9,
            13.0,
            MessierType.OPEN_CLUSTER,
            "Sgr",
        ),
        (
            22,
            "",
            18,
            36,
            23.94,
            -23,
            54,
            17.1,
            5.1,
            32.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            23,
            "",
            17,
            57,
            0.0,
            -18,
            59,
            0.0,
            5.5,
            27.0,
            MessierType.OPEN_CLUSTER,
            "Sgr",
        ),
        (
            24,
            "Sagittarius Star Cloud",
            18,
            16,
            48.0,
            -18,
            29,
            0.0,
            4.6,
            90.0,
            MessierType.STAR_CLOUD,
            "Sgr",
        ),
        (
            25,
            "",
            18,
            31,
            47.0,
            -19,
            7,
            0.0,
            4.6,
            40.0,
            MessierType.OPEN_CLUSTER,
            "Sgr",
        ),
        (
            26,
            "",
            18,
            45,
            12.0,
            -9,
            23,
            0.0,
            8.0,
            15.0,
            MessierType.OPEN_CLUSTER,
            "Sct",
        ),
        (
            27,
            "Dumbbell Nebula",
            19,
            59,
            36.34,
            22,
            43,
            16.1,
            7.4,
            8.0,
            MessierType.NEBULA,
            "Vul",
        ),
        (
            28,
            "",
            18,
            24,
            32.89,
            -24,
            52,
            11.4,
            6.8,
            15.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            29,
            "",
            20,
            24,
            0.0,
            38,
            31,
            24.0,
            6.6,
            7.0,
            MessierType.OPEN_CLUSTER,
            "Cyg",
        ),
        (
            30,
            "",
            21,
            40,
            22.12,
            -23,
            10,
            47.5,
            6.9,
            12.0,
            MessierType.GLOBULAR_CLUSTER,
            "Cap",
        ),
        (
            31,
            "Andromeda Galaxy",
            0,
            42,
            44.3,
            41,
            16,
            9.0,
            3.4,
            178.0,
            MessierType.GALAXY,
            "And",
        ),
        (
            32,
            "",
            0,
            42,
            41.8,
            40,
            51,
            55.0,
            8.1,
            8.0,
            MessierType.GALAXY,
            "And",
        ),
        (
            33,
            "Triangulum Galaxy",
            1,
            33,
            50.9,
            30,
            39,
            37.0,
            5.7,
            73.0,
            MessierType.GALAXY,
            "Tri",
        ),
        (
            34,
            "",
            2,
            42,
            0.0,
            42,
            47,
            0.0,
            5.2,
            35.0,
            MessierType.OPEN_CLUSTER,
            "Per",
        ),
        (
            35,
            "",
            6,
            9,
            0.0,
            24,
            21,
            0.0,
            5.1,
            28.0,
            MessierType.OPEN_CLUSTER,
            "Gem",
        ),
        (
            36,
            "",
            5,
            36,
            18.0,
            34,
            8,
            0.0,
            6.0,
            12.0,
            MessierType.OPEN_CLUSTER,
            "Aur",
        ),
        (
            37,
            "",
            5,
            52,
            18.0,
            32,
            33,
            0.0,
            5.6,
            24.0,
            MessierType.OPEN_CLUSTER,
            "Aur",
        ),
        (
            38,
            "",
            5,
            28,
            42.0,
            35,
            51,
            18.0,
            6.4,
            21.0,
            MessierType.OPEN_CLUSTER,
            "Aur",
        ),
        (
            39,
            "",
            21,
            32,
            12.0,
            48,
            26,
            0.0,
            4.6,
            32.0,
            MessierType.OPEN_CLUSTER,
            "Cyg",
        ),
        (
            40,
            "Winnecke 4",
            12,
            22,
            12.5,
            58,
            5,
            0.0,
            8.4,
            0.8,
            MessierType.DOUBLE_STAR,
            "UMa",
        ),
        (
            41,
            "",
            6,
            46,
            0.0,
            -20,
            45,
            24.0,
            4.5,
            38.0,
            MessierType.OPEN_CLUSTER,
            "CMa",
        ),
        (
            42,
            "Orion Nebula",
            5,
            35,
            17.3,
            -5,
            23,
            28.0,
            4.0,
            85.0,
            MessierType.NEBULA,
            "Ori",
        ),
        (
            43,
            "De Mairan's Nebula",
            5,
            35,
            31.0,
            -5,
            16,
            0.0,
            9.0,
            20.0,
            MessierType.NEBULA,
            "Ori",
        ),
        (
            44,
            "Beehive Cluster",
            8,
            40,
            24.0,
            19,
            41,
            0.0,
            3.1,
            95.0,
            MessierType.OPEN_CLUSTER,
            "Cnc",
        ),
        (
            45,
            "Pleiades",
            3,
            47,
            24.0,
            24,
            7,
            0.0,
            1.6,
            110.0,
            MessierType.OPEN_CLUSTER,
            "Tau",
        ),
        (
            46,
            "",
            7,
            41,
            46.0,
            -14,
            48,
            36.0,
            6.1,
            27.0,
            MessierType.OPEN_CLUSTER,
            "Pup",
        ),
        (
            47,
            "",
            7,
            36,
            35.0,
            -14,
            28,
            0.0,
            4.4,
            30.0,
            MessierType.OPEN_CLUSTER,
            "Pup",
        ),
        (
            48,
            "",
            8,
            13,
            43.0,
            -5,
            45,
            0.0,
            5.8,
            54.0,
            MessierType.OPEN_CLUSTER,
            "Hya",
        ),
        (
            49,
            "",
            12,
            29,
            46.7,
            8,
            0,
            2.0,
            8.4,
            10.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            50,
            "",
            7,
            2,
            47.0,
            -8,
            23,
            0.0,
            5.9,
            16.0,
            MessierType.OPEN_CLUSTER,
            "Mon",
        ),
        (
            51,
            "Whirlpool Galaxy",
            13,
            29,
            52.7,
            47,
            11,
            43.0,
            8.4,
            11.0,
            MessierType.GALAXY,
            "CVn",
        ),
        (
            52,
            "",
            23,
            24,
            48.0,
            61,
            35,
            36.0,
            6.9,
            13.0,
            MessierType.OPEN_CLUSTER,
            "Cas",
        ),
        (
            53,
            "",
            13,
            12,
            55.25,
            18,
            10,
            9.0,
            7.6,
            13.0,
            MessierType.GLOBULAR_CLUSTER,
            "Com",
        ),
        (
            54,
            "",
            18,
            55,
            3.33,
            -30,
            28,
            47.5,
            7.6,
            12.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            55,
            "",
            19,
            39,
            59.71,
            -30,
            57,
            53.1,
            6.3,
            19.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            56,
            "",
            19,
            16,
            35.57,
            30,
            11,
            0.6,
            8.3,
            8.8,
            MessierType.GLOBULAR_CLUSTER,
            "Lyr",
        ),
        (
            57,
            "Ring Nebula",
            18,
            53,
            35.08,
            33,
            1,
            45.0,
            8.8,
            1.4,
            MessierType.NEBULA,
            "Lyr",
        ),
        (
            58,
            "",
            12,
            37,
            43.5,
            11,
            49,
            5.0,
            9.7,
            5.5,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            59,
            "",
            12,
            42,
            2.3,
            11,
            38,
            49.0,
            9.6,
            5.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            60,
            "",
            12,
            43,
            40.0,
            11,
            33,
            9.0,
            8.8,
            7.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            61,
            "",
            12,
            21,
            54.9,
            4,
            28,
            25.0,
            9.7,
            6.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            62,
            "",
            17,
            1,
            12.60,
            -30,
            6,
            44.5,
            6.5,
            15.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            63,
            "Sunflower Galaxy",
            13,
            15,
            49.3,
            42,
            1,
            45.0,
            8.6,
            12.0,
            MessierType.GALAXY,
            "CVn",
        ),
        (
            64,
            "Black Eye Galaxy",
            12,
            56,
            43.7,
            21,
            40,
            58.0,
            8.5,
            10.0,
            MessierType.GALAXY,
            "Com",
        ),
        (
            65,
            "",
            11,
            18,
            55.9,
            13,
            5,
            32.0,
            9.3,
            8.0,
            MessierType.GALAXY,
            "Leo",
        ),
        (
            66,
            "",
            11,
            20,
            15.0,
            12,
            59,
            28.0,
            8.9,
            9.0,
            MessierType.GALAXY,
            "Leo",
        ),
        (
            67,
            "",
            8,
            51,
            18.0,
            11,
            48,
            0.0,
            6.9,
            30.0,
            MessierType.OPEN_CLUSTER,
            "Cnc",
        ),
        (
            68,
            "",
            12,
            39,
            27.98,
            -26,
            44,
            38.6,
            7.8,
            12.0,
            MessierType.GLOBULAR_CLUSTER,
            "Hya",
        ),
        (
            69,
            "",
            18,
            31,
            23.10,
            -32,
            20,
            53.1,
            7.6,
            10.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            70,
            "",
            18,
            43,
            12.76,
            -32,
            17,
            31.6,
            7.9,
            8.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            71,
            "",
            19,
            53,
            46.49,
            18,
            46,
            45.1,
            8.2,
            7.2,
            MessierType.GLOBULAR_CLUSTER,
            "Sge",
        ),
        (
            72,
            "",
            20,
            53,
            27.70,
            -12,
            32,
            13.4,
            9.3,
            6.6,
            MessierType.GLOBULAR_CLUSTER,
            "Aqr",
        ),
        (
            73,
            "",
            20,
            59,
            0.0,
            -12,
            38,
            0.0,
            9.0,
            2.8,
            MessierType.OPEN_CLUSTER,
            "Aqr",
        ),
        (
            74,
            "",
            1,
            36,
            41.8,
            15,
            47,
            1.0,
            9.4,
            10.0,
            MessierType.GALAXY,
            "Psc",
        ),
        (
            75,
            "",
            20,
            6,
            4.92,
            -21,
            55,
            17.9,
            8.5,
            6.8,
            MessierType.GLOBULAR_CLUSTER,
            "Sgr",
        ),
        (
            76,
            "Little Dumbbell",
            1,
            42,
            19.0,
            51,
            34,
            31.0,
            10.1,
            2.7,
            MessierType.NEBULA,
            "Per",
        ),
        (
            77,
            "",
            2,
            42,
            40.8,
            -0,
            0,
            48.0,
            8.9,
            7.0,
            MessierType.GALAXY,
            "Cet",
        ),
        (78, "", 5, 46, 45.8, 0, 4, 45.0, 8.3, 8.0, MessierType.NEBULA, "Ori"),
        (
            79,
            "",
            5,
            24,
            10.59,
            -24,
            31,
            27.3,
            7.7,
            9.6,
            MessierType.GLOBULAR_CLUSTER,
            "Lep",
        ),
        (
            80,
            "",
            16,
            17,
            2.41,
            -22,
            58,
            30.9,
            7.3,
            10.0,
            MessierType.GLOBULAR_CLUSTER,
            "Sco",
        ),
        (
            81,
            "Bode's Galaxy",
            9,
            55,
            33.2,
            69,
            3,
            55.0,
            6.9,
            26.0,
            MessierType.GALAXY,
            "UMa",
        ),
        (
            82,
            "Cigar Galaxy",
            9,
            55,
            52.2,
            69,
            40,
            47.0,
            8.4,
            11.0,
            MessierType.GALAXY,
            "UMa",
        ),
        (
            83,
            "Southern Pinwheel",
            13,
            37,
            0.9,
            -29,
            51,
            57.0,
            7.6,
            11.0,
            MessierType.GALAXY,
            "Hya",
        ),
        (
            84,
            "",
            12,
            25,
            3.7,
            12,
            53,
            13.0,
            9.1,
            6.5,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            85,
            "",
            12,
            25,
            24.0,
            18,
            11,
            28.0,
            9.1,
            7.0,
            MessierType.GALAXY,
            "Com",
        ),
        (
            86,
            "",
            12,
            26,
            11.7,
            12,
            56,
            46.0,
            8.9,
            8.9,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            87,
            "Virgo A",
            12,
            30,
            49.4,
            12,
            23,
            28.0,
            8.6,
            8.3,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            88,
            "",
            12,
            31,
            59.2,
            14,
            25,
            14.0,
            9.6,
            7.0,
            MessierType.GALAXY,
            "Com",
        ),
        (
            89,
            "",
            12,
            35,
            39.8,
            12,
            33,
            23.0,
            9.8,
            5.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            90,
            "",
            12,
            36,
            49.8,
            13,
            9,
            46.0,
            9.5,
            9.5,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            91,
            "",
            12,
            35,
            26.4,
            14,
            29,
            47.0,
            10.2,
            5.4,
            MessierType.GALAXY,
            "Com",
        ),
        (
            92,
            "",
            17,
            17,
            7.39,
            43,
            8,
            9.4,
            6.4,
            14.0,
            MessierType.GLOBULAR_CLUSTER,
            "Her",
        ),
        (
            93,
            "",
            7,
            44,
            29.0,
            -23,
            51,
            24.0,
            6.2,
            22.0,
            MessierType.OPEN_CLUSTER,
            "Pup",
        ),
        (
            94,
            "",
            12,
            50,
            53.1,
            41,
            7,
            14.0,
            8.2,
            11.0,
            MessierType.GALAXY,
            "CVn",
        ),
        (
            95,
            "",
            10,
            43,
            57.7,
            11,
            42,
            14.0,
            9.7,
            7.0,
            MessierType.GALAXY,
            "Leo",
        ),
        (
            96,
            "",
            10,
            46,
            45.7,
            11,
            49,
            12.0,
            9.2,
            7.0,
            MessierType.GALAXY,
            "Leo",
        ),
        (
            97,
            "Owl Nebula",
            11,
            14,
            47.7,
            55,
            1,
            9.0,
            9.9,
            3.4,
            MessierType.NEBULA,
            "UMa",
        ),
        (
            98,
            "",
            12,
            13,
            48.3,
            14,
            54,
            1.0,
            10.1,
            9.5,
            MessierType.GALAXY,
            "Com",
        ),
        (
            99,
            "",
            12,
            18,
            49.6,
            14,
            25,
            0.0,
            9.9,
            5.4,
            MessierType.GALAXY,
            "Com",
        ),
        (
            100,
            "",
            12,
            22,
            54.9,
            15,
            49,
            21.0,
            9.3,
            7.0,
            MessierType.GALAXY,
            "Com",
        ),
        (
            101,
            "Pinwheel Galaxy",
            14,
            3,
            12.6,
            54,
            20,
            57.0,
            7.9,
            29.0,
            MessierType.GALAXY,
            "UMa",
        ),
        (
            102,
            "",
            15,
            6,
            29.5,
            55,
            45,
            48.0,
            9.9,
            6.0,
            MessierType.GALAXY,
            "Dra",
        ),
        (
            103,
            "",
            1,
            33,
            23.0,
            60,
            39,
            0.0,
            7.4,
            6.0,
            MessierType.OPEN_CLUSTER,
            "Cas",
        ),
        (
            104,
            "Sombrero Galaxy",
            12,
            39,
            59.4,
            -11,
            37,
            23.0,
            8.0,
            9.0,
            MessierType.GALAXY,
            "Vir",
        ),
        (
            105,
            "",
            10,
            47,
            49.6,
            12,
            34,
            54.0,
            9.3,
            5.0,
            MessierType.GALAXY,
            "Leo",
        ),
        (
            106,
            "",
            12,
            18,
            57.5,
            47,
            18,
            14.0,
            8.4,
            19.0,
            MessierType.GALAXY,
            "CVn",
        ),
        (
            107,
            "",
            16,
            32,
            31.86,
            -13,
            3,
            13.6,
            7.9,
            13.0,
            MessierType.GLOBULAR_CLUSTER,
            "Oph",
        ),
        (
            108,
            "",
            11,
            11,
            31.0,
            55,
            40,
            27.0,
            10.0,
            8.0,
            MessierType.GALAXY,
            "UMa",
        ),
        (
            109,
            "",
            11,
            57,
            36.0,
            53,
            22,
            28.0,
            9.8,
            7.0,
            MessierType.GALAXY,
            "UMa",
        ),
        (
            110,
            "",
            0,
            40,
            22.1,
            41,
            41,
            7.0,
            8.5,
            17.0,
            MessierType.GALAXY,
            "And",
        ),
    ]

    def __init__(self):
        """Initialize the Messier catalog."""

        self._catalog_array = None
        self._build_catalog()

    def _build_catalog(self):
        """Build the structured NumPy array from catalog data."""

        MESSIER_DTYPE = np.dtype(
            [
                ("m_number", np.int32),
                ("name", "U50"),
                ("ra", np.float64),  # Right ascension in radians
                ("dec", np.float64),  # Declination in radians
                ("x", np.float64),  # ECI x-coordinate
                ("y", np.float64),  # ECI y-coordinate
                ("z", np.float64),  # ECI z-coordinate
                ("v_mag", np.float32),  # Visual magnitude
                ("size", np.float32),  # Angular size in arcminutes
                ("obj_type", np.int32),  # Object type (MessierType enum value)
                ("constellation", "U5"),  # Constellation abbreviation
            ]
        )

        n_objects = len(self.MESSIER_DATA)
        self._catalog_array = np.zeros(n_objects, dtype=MESSIER_DTYPE)

        for i, obj_data in enumerate(self.MESSIER_DATA):
            (
                m_num,
                name,
                ra_h,
                ra_m,
                ra_s,
                dec_d,
                dec_m,
                dec_s,
                mag,
                size,
                obj_type,
                const,
            ) = obj_data

            # Convert RA from hours/min/sec to radians
            ra_hours = ra_h + ra_m / 60.0 + ra_s / 3600.0
            ra_rad = np.deg2rad(ra_hours * 15.0)  # 15 degrees per hour

            # Convert Dec from degrees/min/sec to radians
            dec_sign = 1 if dec_d >= 0 else -1
            dec_deg = abs(dec_d) + dec_m / 60.0 + dec_s / 3600.0
            dec_rad = np.deg2rad(dec_deg * dec_sign)

            # Convert to ECI (Earth-Centered Inertial) coordinates
            x = np.cos(dec_rad) * np.cos(ra_rad)
            y = np.cos(dec_rad) * np.sin(ra_rad)
            z = np.sin(dec_rad)

            # Fill catalog entry
            self._catalog_array[i]["m_number"] = m_num
            self._catalog_array[i]["name"] = name
            self._catalog_array[i]["ra"] = ra_rad
            self._catalog_array[i]["dec"] = dec_rad
            self._catalog_array[i]["x"] = x
            self._catalog_array[i]["y"] = y
            self._catalog_array[i]["z"] = z
            self._catalog_array[i]["v_mag"] = mag
            self._catalog_array[i]["size"] = size
            self._catalog_array[i]["obj_type"] = obj_type
            self._catalog_array[i]["constellation"] = const

    def get_all_objects(self) -> NDArray:
        """Get all Messier objects."""
        return self._catalog_array.copy()

    def get_object_by_number(self, m_number: int) -> Optional[NDArray]:
        """Get a specific Messier object by its M number.

        :param m_number: Messier object's M number.
        :type m_number: int

        :return: object information
        :rtype: NDArray | None
        """
        mask = self._catalog_array["m_number"] == m_number
        result = self._catalog_array[mask]
        return result[0] if len(result) > 0 else None

    def get_objects_by_type(self, obj_type: MessierType) -> NDArray:
        """Get all Messier objects of a specific type.

        :param obj_type: type of Messier objects
        :type obj_type: MessierType

        :return: objects of the desired type
        :rtype: NDArray
        """
        mask = self._catalog_array["obj_type"] == obj_type
        return self._catalog_array[mask].copy()

    def get_objects_by_constellation(self, constellation: str) -> NDArray:
        """Get all Messier objects in a specific constellation.

        :param constellation: constellation name (3-letter latin abbreviation)
        :type constellation: str

        :return: objects of the desired constellation
        :rtype: NDArray
        """
        mask = self._catalog_array["constellation"] == constellation.upper()
        return self._catalog_array[mask].copy()

    def get_objects_by_magnitude(
        self, min_mag: float = -30.0, max_mag: float = 30.0
    ) -> NDArray:
        """Get Messier objects within a magnitude range.

        :param min_mag: low boundary of magnitude
        :type min_mag: float:  (Default value = -30.0)
        :param max_mag: high boundary of magnitude
        :type max_mag: float:  (Default value = 30.0)

        :return: objects of the desired magnitude
        :rtype: NDArray
        """
        mask = (self._catalog_array["v_mag"] >= min_mag) & (
            self._catalog_array["v_mag"] <= max_mag
        )
        return self._catalog_array[mask].copy()

    def get_brightest_objects(self, n: int = 10) -> NDArray:
        """Get the n the brightest Messier objects.

        :param n: number of objects to return
        :type n: int:  (Default value = 10)

        :return: array with the top n the brightest Messier objects
        :rtype: NDArray
        """
        sorted_indices = np.argsort(self._catalog_array["v_mag"])
        return self._catalog_array[sorted_indices[:n]].copy()

    def get_largest_objects(self, n: int = 10) -> NDArray:
        """Get the n largest Messier objects by angular size.

        :param n: number of objects to return
        :type n: int:  (Default value = 10)

        :return: array with the largest n Messier objects
        :rtype: NDArray
        """
        sorted_indices = np.argsort(self._catalog_array["size"])[::-1]
        return self._catalog_array[sorted_indices[:n]].copy()

    def search_by_name(self, name: str) -> NDArray:
        """Search for Messier objects by name.

        :param name: name of the Messier object
        :type name: str

        :return: information about the Messier object
        :rtype: NDArray
        """

        name_lower = name.lower()
        mask = np.array(
            [
                name_lower in obj_name.lower()
                for obj_name in self._catalog_array["name"]
            ]
        )
        return self._catalog_array[mask].copy()

    def get_statistics(self) -> dict:
        """Get statistics about the Messier catalog."""

        stats = {
            "total_objects": len(self._catalog_array),
            "galaxies": np.sum(
                self._catalog_array["obj_type"] == MessierType.GALAXY
            ),
            "globular_clusters": np.sum(
                self._catalog_array["obj_type"] == MessierType.GLOBULAR_CLUSTER
            ),
            "open_clusters": np.sum(
                self._catalog_array["obj_type"] == MessierType.OPEN_CLUSTER
            ),
            "nebulae": np.sum(
                self._catalog_array["obj_type"] == MessierType.NEBULA
            ),
            "supernova_remnants": np.sum(
                self._catalog_array["obj_type"]
                == MessierType.SUPERNOVA_REMNANT
            ),
            "star_clouds": np.sum(
                self._catalog_array["obj_type"] == MessierType.STAR_CLOUD
            ),
            "brightest": self._catalog_array[
                np.argmin(self._catalog_array["v_mag"])
            ],
            "dimmest": self._catalog_array[
                np.argmax(self._catalog_array["v_mag"])
            ],
            "largest": self._catalog_array[
                np.argmax(self._catalog_array["size"])
            ],
        }
        return stats

    @staticmethod
    def get_type_name(obj_type: MessierType) -> str:
        """Get the human-readable name for an object type.

        :param obj_type: type of the objects
        :type obj_type: MessierType

        :return: name
        :rtype: str
        """

        type_names = {
            MessierType.GALAXY: "Galaxy",
            MessierType.GLOBULAR_CLUSTER: "Globular Cluster",
            MessierType.OPEN_CLUSTER: "Open Cluster",
            MessierType.NEBULA: "Nebula",
            MessierType.SUPERNOVA_REMNANT: "Supernova Remnant",
            MessierType.STAR_CLOUD: "Star Cloud",
            MessierType.DOUBLE_STAR: "Double Star",
        }
        return type_names.get(obj_type, "Unknown")

    @staticmethod
    def get_type_color(obj_type: MessierType) -> str:
        """Get a suggested color for visualizing an object type.

        :param obj_type: type of objects
        :type obj_type: MessierType

        :return: RGB color
        :rtype: str
        """
        type_colors = {
            MessierType.GALAXY:            "#FF6B9D",
            MessierType.GLOBULAR_CLUSTER:  "#FFD700",
            MessierType.OPEN_CLUSTER:      "#87CEEB",
            MessierType.NEBULA:            "#00CED1",
            MessierType.SUPERNOVA_REMNANT: "#FF4500",
            MessierType.STAR_CLOUD:        "#DDA0DD",
            MessierType.DOUBLE_STAR:       "#FFFDE7",
        }
        return type_colors.get(obj_type, "#FFFFFF")


def print_catalog_info():
    """Print information about the Messier catalog."""

    catalog = MessierCatalog()
    stats = catalog.get_statistics()

    print("=" * 60)
    print("MESSIER CATALOG INFORMATION")
    print("=" * 60)
    print(f"Total objects: {stats['total_objects']}")
    print("\nObjects by type:")
    print(f"  Galaxies: {stats['galaxies']}")
    print(f"  Globular Clusters: {stats['globular_clusters']}")
    print(f"  Open Clusters: {stats['open_clusters']}")
    print(f"  Nebulae: {stats['nebulae']}")
    print(f"  Supernova Remnants: {stats['supernova_remnants']}")
    print(f"  Star Clouds: {stats['star_clouds']}")

    print("\nBrightest object:")
    brightest = stats["brightest"]
    print(f"  M{brightest['m_number']}: {brightest['name'] or '(unnamed)'}")
    print(f"  Magnitude: {brightest['v_mag']:.1f}")
    print(
        f"  Type: "
        f"{MessierCatalog.get_type_name(MessierType(brightest['obj_type']))}"
    )

    print("\nLargest object:")
    largest = stats["largest"]
    print(f"  M{largest['m_number']}: {largest['name'] or '(unnamed)'}")
    print(f"  Size: {largest['size']:.1f} arcminutes")
    print(
        f"  Type: "
        f"{MessierCatalog.get_type_name(MessierType(largest['obj_type']))}"
    )

    print("\n" + "=" * 60)

    # Show top 10 brightest objects
    print("\nTop 10 Brightest Messier Objects:")
    print("-" * 60)
    brightest_objs = catalog.get_brightest_objects(10)
    for obj in brightest_objs:
        name_str = f" - {obj['name']}" if obj["name"] else ""
        type_str = MessierCatalog.get_type_name(MessierType(obj["obj_type"]))
        print(
            f"  M{obj['m_number']:3d}{name_str:25s} | "
            f"Mag: {obj['v_mag']:4.1f} | {type_str}"
        )

    print("=" * 60)


if __name__ == "__main__":
    print_catalog_info()
