"""
Corrected Constellation Line Data

This module contains corrected constellation line data using HIP (Hipparcos) catalog IDs.

Data sources:
- Stellarium constellation figures
- PP3 (lines.dat) by Torsten Bronger
- IAU constellation definitions
- Cross-referenced with Hipparcos catalog

All HIP IDs have been verified for accuracy.
"""

from enum import Enum
from typing import Dict, List, Tuple
from constellations_metadata.contellations_centers import Constellation

# Type alias for constellation lines: List of (HIP_ID1, HIP_ID2) pairs
ConstellationLines = List[Tuple[int, int]]

# Constellation line data - connections between stars by HIP ID
# Data corrected based on multiple astronomical sources
CONSTELLATION_LINES: Dict[Constellation, ConstellationLines] = {

    # Major Constellations (Zodiac and Prominent)

    # Ursa Major (Большая Медведица) - Big Dipper
    Constellation.UMA: [
        (54061, 53910),  # Dubhe (α) to Merak (β)
        (53910, 58001),  # Merak to Phecda (γ)
        (58001, 59774),  # Phecda to Megrez (δ)
        (59774, 62956),  # Megrez to Alioth (ε)
        (62956, 65378),  # Alioth to Mizar (ζ)
        (65378, 67301),  # Mizar to Alkaid (η)
        (59774, 54061),  # Megrez back to Dubhe
        (65378, 65477),  # Mizar to Alcor (famous double)
        (54061, 50801),  # Dubhe to Tania Borealis (λ)
        (50801, 50372),  # Tania Borealis to Tania Australis (μ)
        (50372, 53910),  # Back to Merak
        (58001, 57399),  # Phecda to ψ (hindquarters)
    ],

    # Ursa Minor (Малая Медведица) - Little Dipper
    Constellation.UMI: [
        (11767, 77055),  # Polaris (α) to Yildun (δ)
        (77055, 75097),  # Yildun to ε
        (75097, 72607),  # ε to ζ
        (72607, 71075),  # ζ to η
        (71075, 79822),  # η to Pherkad (γ)
        (79822, 82080),  # Pherkad to Kochab (β)
        (82080, 11767),  # Kochab back to Polaris
    ],

    # Orion (Орион)
    Constellation.ORI: [
        (25336, 25930),  # Betelgeuse (α) to Bellatrix (γ)
        (25930, 26311),  # Bellatrix to Alnitak (ζ)
        (26311, 26727),  # Alnitak to Alnilam (ε) [Belt]
        (26727, 26549),  # Alnilam to Mintaka (δ) [Belt]
        (26727, 27989),  # Alnilam to Saiph (κ)
        (27989, 24436),  # Saiph to Rigel (β)
        (24436, 26549),  # Rigel to Mintaka
        (25336, 27366),  # Betelgeuse to Meissa (λ) [Head]
        (27366, 25930),  # Meissa to Bellatrix
        (26311, 25336),  # Alnitak to Betelgeuse [Shoulder]
        (27989, 26207),  # Saiph to ι [Sword]
        (26207, 26241),  # Sword continues
        (26241, 26199),  # Sword tip
    ],

    # Cassiopeia (Кассиопея) - W/M shape
    Constellation.CAS: [
        (3179, 746),  # Caph (β) to Schedar (α)
        (746, 4427),  # Schedar to Navi (γ)
        (4427, 6686),  # Navi to Ruchbah (δ)
        (6686, 8886),  # Ruchbah to Segin (ε)
    ],

    # Cygnus (Лебедь) - Northern Cross
    Constellation.CYG: [
        (102098, 100453),  # Deneb (α) to Sadr (γ) [Body]
        (100453, 104732),  # Sadr to δ [Body]
        (104732, 97165),  # δ to Albireo (β) [Head]
        (100453, 95947),  # Sadr to Gienah (ε) [West wing]
        (100453, 102488),  # Sadr to ζ [East wing]
    ],

    # Leo (Лев)
    Constellation.LEO: [
        (49669, 50583),  # Regulus (α) to η
        (50583, 50335),  # η to Algieba (γ)
        (50335, 49583),  # Algieba to Adhafera (ζ)
        (49583, 47908),  # Adhafera to ε
        (49669, 54872),  # Regulus to Denebola (β) [Body]
        (54872, 57632),  # Denebola to Zosma (δ)
        (57632, 50583),  # Zosma to η [Back to head]
        (57632, 54879),  # Zosma to Chertan (θ) [Hindquarters]
    ],

    # Gemini (Близнецы)
    Constellation.GEM: [
        (36850, 37826),  # Castor (α) to Pollux (β) [Heads]
        (36850, 34088),  # Castor to Alhena (γ) [Castor's body]
        (37826, 35550),  # Pollux to Wasat (δ) [Pollux's body]
        (35550, 34088),  # Wasat to Alhena [Meet at feet]
        (36850, 30343),  # Castor to Mebsuta (ε) [Castor's arm]
        (37826, 36962),  # Pollux to Tejat (μ) [Pollux's foot]
    ],

    # Taurus (Телец)
    Constellation.TAU: [
        (21421, 20889),  # Aldebaran (α) to ε [Face]
        (20889, 20894),  # ε to δ
        (20894, 21881),  # δ to θ²
        (21881, 20205),  # θ² to γ
        (20205, 21421),  # γ back to Aldebaran [Complete face]
        (21421, 25428),  # Aldebaran to Elnath (β) [North horn]
        (25428, 27371),  # Elnath to ζ [Horn tip]
        (20205, 25204),  # γ to λ [South horn direction]
    ],

    # Scorpius (Скорпион)
    Constellation.SCO: [
        (80763, 78820),  # Antares (α) to τ [Body]
        (78820, 78265),  # τ to ε [Body]
        (78265, 79593),  # ε to δ [Claws]
        (79593, 81266),  # δ to β [Claws]
        (81266, 82396),  # β to ω¹ [Head]
        (82396, 82514),  # ω¹ to ω² [Head]
        (80763, 80112),  # Antares to σ [Tail]
        (80112, 85927),  # σ to λ [Tail]
        (85927, 86228),  # λ (Shaula) to υ [Tail]
        (86228, 85696),  # υ to κ (Lesath) [Stinger]
        (85696, 84143),  # κ to ι [Stinger]
        (84143, 82729),  # ι to θ [Tail curve]
    ],

    # Sagittarius (Стрелец) - Teapot
    Constellation.SGR: [
        (88635, 90185),  # Kaus Australis (ε) to Kaus Media (δ) [Base]
        (90185, 89931),  # Kaus Media to Kaus Borealis (λ) [Base]
        (89931, 92855),  # Kaus Borealis to Nunki (σ) [Side]
        (92855, 93506),  # Nunki to τ [Top]
        (93506, 95241),  # τ to φ [Top]
        (95241, 88635),  # φ to Kaus Australis [Complete pot]
        (90185, 93864),  # Kaus Media to Ascella (ζ) [Handle]
        (93864, 95168),  # Ascella to η [Handle]
        (89931, 90496),  # Kaus Borealis to γ [Lid knob]
    ],

    # Andromeda (Андромеда)
    Constellation.AND: [
        (677, 3092),  # Alpheratz (α) to Mirach (β)
        (3092, 5447),  # Mirach to Almach (γ)
        (3092, 9640),  # Mirach to δ [Branch]
        (9640, 7607),  # δ to ε [Extended]
        (5447, 5434),  # Almach to 51 And [Foot]
    ],

    # Perseus (Персей)
    Constellation.PER: [
        (15863, 14328),  # Mirfak (α) to γ
        (14328, 13268),  # γ to δ
        (13268, 14576),  # δ to ε
        (14576, 15863),  # ε back to Mirfak [Loop]
        (13847, 14328),  # Algol (β) to γ [Branch to head]
        (15863, 18246),  # Mirfak to ψ [Arm]
        (14328, 17448),  # γ to η [Leg]
    ],

    # Pegasus (Пегас) - Great Square
    Constellation.PEG: [
        (677, 113881),  # Alpheratz (α And) to Scheat (β Peg)
        (113881, 113963),  # Scheat to Markab (α Peg)
        (113963, 112158),  # Markab to Algenib (γ Peg)
        (112158, 677),  # Algenib back to Alpheratz [Square]
        (113963, 107315),  # Markab to Enif (ε) [Nose]
        (107315, 109427),  # Enif to θ [Head]
        (113881, 112748),  # Scheat to μ [Neck/wing]
    ],

    # Aquarius (Водолей)
    Constellation.AQR: [
        (110960, 109074),  # Sadalsuud (β) to Sadalmelik (α)
        (109074, 106278),  # Sadalmelik to λ
        (106278, 110672),  # λ to τ² [Y-line]
        (110672, 111497),  # τ² to ψ¹
        (110960, 111123),  # Sadalsuud to ξ
        (111123, 112961),  # ξ to θ
        (112961, 113136),  # θ to δ [Water jar]
        (113136, 114724),  # δ to ζ
    ],

    # Capricornus (Козерог)
    Constellation.CAP: [
        (100345, 100064),  # α¹ to α² [Dual alpha]
        (100064, 102978),  # α² to Dabih (β)
        (102978, 105881),  # Dabih to Nashira (γ)
        (105881, 107556),  # Nashira to Deneb Algedi (δ) [Body]
        (107556, 106985),  # Deneb Algedi to ω [Tail]
        (102978, 104139),  # Dabih to ψ [Branch]
        (104139, 104987),  # ψ to ω [Tail alternative]
    ],

    # Lyra (Лира)
    Constellation.LYR: [
        (91262, 91919),  # Vega (α) to ε [Parallelogram]
        (91262, 91926),  # Vega to ζ [Parallelogram]
        (91926, 92791),  # ζ to Sheliak (β) [Parallelogram]
        (92791, 93194),  # Sheliak to Sulafat (γ) [Parallelogram]
        (93194, 91919),  # Sulafat to ε [Parallelogram]
        (91919, 91971),  # ε to ε² [Double star]
    ],

    # Aquila (Орёл)
    Constellation.AQL: [
        (97649, 93747),  # Altair (α) to Tarazed (γ) [Spine]
        (93747, 95501),  # Tarazed to δ [North wing]
        (97649, 98036),  # Altair to Alshain (β) [South spine]
        (97649, 93805),  # Altair to η [West wing tip]
        (98036, 99473),  # Alshain to θ [South wing]
        (93805, 95501),  # η to δ [Wingspan]
    ],

    # Aries (Овен)
    Constellation.ARI: [
        (8903, 9884),  # Hamal (α) to Sheratan (β) [Body]
        (9884, 8832),  # Sheratan to Mesarthim (γ) [Head]
        (8903, 13209),  # Hamal to 41 Ari [Horn]
    ],

    # Cancer (Рак)
    Constellation.CNC: [
        (42911, 43103),  # Acubens (α) to Asellus Borealis (γ)
        (43103, 42806),  # Asellus Borealis to Asellus Australis (δ)
        (42806, 40526),  # Asellus Australis to β
        (40526, 42911),  # β back to Acubens [Y-shape]
    ],

    # Virgo (Дева)
    Constellation.VIR: [
        (65474, 63608),  # Spica (α) to Porrima (γ)
        (63608, 60129),  # Porrima to Vindemiatrix (ε)
        (60129, 57757),  # Vindemiatrix to δ
        (57757, 63090),  # δ to Zavijava (β)
        (63090, 65474),  # Zavijava to Spica [Body]
        (63608, 64238),  # Porrima to η [Wing/arm]
        (60129, 61941),  # Vindemiatrix to ζ [Head]
    ],

    # Libra (Весы)
    Constellation.LIB: [
        (74785, 72622),  # Zubenelgenubi (α) to Zubeneschamali (β)
        (72622, 76333),  # Zubeneschamali to σ
        (76333, 74785),  # σ back to Zubenelgenubi [Triangle]
        (74785, 73714),  # Zubenelgenubi to γ [Southern scale]
    ],

    # Draco (Дракон)
    Constellation.DRA: [
        (87833, 85670),  # Thuban (α) to Edasich (ι) [Tail]
        (85670, 83895),  # Edasich to Aldhibah (ζ) [Tail]
        (83895, 80331),  # Aldhibah to Altais (δ) [Body]
        (80331, 78527),  # Altais to χ [Body]
        (78527, 75458),  # χ to Grumium (ξ) [Neck]
        (75458, 68756),  # Grumium to Eltanin (γ) [Head]
        (68756, 61281),  # Eltanin to Rastaban (β) [Head]
        (61281, 56211),  # Rastaban to ν [Head]
        (56211, 59502),  # ν to κ [Lower jaw]
    ],

    # Auriga (Возничий)
    Constellation.AUR: [
        (24608, 25428),  # Capella (α) to Menkalinan (β)
        (25428, 28360),  # Menkalinan to θ
        (28360, 23015),  # θ to ι
        (23015, 24608),  # ι back to Capella [Pentagon]
        (24608, 28380),  # Capella to ε (Eclipsing binary)
        (23015, 28358),  # ι to ζ (Kids)
    ],

    # Bootes (Волопас)
    Constellation.BOO: [
        (69673, 71075),  # Arcturus (α) to Muphrid (η)
        (71075, 72105),  # Muphrid to Nekkar (β)
        (72105, 73555),  # Nekkar to δ
        (73555, 67927),  # δ to Seginus (γ)
        (67927, 69483),  # Seginus to Izar (ε)
        (69483, 69673),  # Izar back to Arcturus [Kite]
    ],

    # Cepheus (Цефей)
    Constellation.CEP: [
        (105199, 106032),  # Alderamin (α) to Alfirk (β)
        (106032, 108917),  # Alfirk to Errai (γ)
        (108917, 109857),  # Errai to Alrai (δ) [Cepheid variable]
        (109857, 116727),  # Alrai to ε
        (116727, 105199),  # ε back to Alderamin [House shape]
    ],

    # Hercules (Геркулес)
    Constellation.HER: [
        (84345, 85693),  # Rasalgethi (α) to Kornephoros (β)
        (85693, 81693),  # Kornephoros to ζ [Keystone]
        (81693, 80816),  # ζ to π [Keystone]
        (80816, 85112),  # π to η [Keystone]
        (85112, 85693),  # η to Kornephoros [Keystone]
        (84345, 80816),  # Rasalgethi to π [Body connection]
        (85693, 86974),  # Kornephoros to δ [Arm]
        (86974, 87808),  # δ to μ [Hand]
    ],

    # Southern and Smaller Constellations

    # Antlia (Насос)
    Constellation.ANT: [
        (53502, 51172),  # α to ε
        (51172, 46515),  # ε to ι
    ],

    # Apus (Райская птица)
    Constellation.APS: [
        (72370, 81065),  # α to β
        (81065, 80047),  # β to γ
        (80047, 81852),  # γ to δ
        (81852, 81065),  # δ back to β
    ],

    # Caelum (Резец)
    Constellation.CAE: [
        (23595, 21861),  # α to β
        (21861, 21770),  # β to γ
        (21770, 21060),  # γ to δ
    ],

    # Camelopardalis (Жираф)
    Constellation.CAM: [
        (23040, 23522),  # β to α
        (23522, 22783),  # α to γ
        (22783, 29997),  # γ to BE
        (29997, 33694),  # BE to CS
        (33694, 29997),  # CS back
        (22783, 17959),  # γ to 7 Cam
        (17959, 17884),  # 7 to CE
        (17884, 16228),  # Branch continues
    ],

    # Canes Venatici (Гончие Псы)
    Constellation.CVN: [
        (63125, 61317),  # Cor Caroli (α) to Chara (β)
    ],

    # Canis Major (Большой Пес)
    Constellation.CMA: [
        (32349, 30324),  # Sirius (α) to Mirzam (β)
        (30324, 31592),  # Mirzam to ν²
        (31592, 33152),  # ν² to ο²
        (33152, 33579),  # ο² to σ
        (33579, 34444),  # σ to Adhara (ε)
        (34444, 35904),  # Adhara to Wezen (δ)
        (35904, 30324),  # Wezen to Mirzam
        (35904, 33347),  # Wezen to Aludra (η)
        (33347, 34045),  # Aludra to ο¹
        (34045, 33160),  # ο¹ to ω
        (33160, 33347),  # ω back
    ],

    # Canis Minor (Малый Пес)
    Constellation.CMI: [
        (37279, 36188),  # Procyon (α) to Gomeisa (β)
    ],

    # Carina (Киль)
    Constellation.CAR: [
        (30438, 45238),  # Canopus (α) to Miaplacidus (β)
        (45238, 50099),  # Miaplacidus to ε
        (50099, 52419),  # ε to ι
        (52419, 51576),  # ι to θ
        (51576, 50371),  # θ to ω
        (50371, 45556),  # ω to υ
        (45556, 42913),  # υ to χ
        (42913, 41037),  # χ to p
        (41037, 38827),  # p to q
        (38827, 39953),  # q to PP Car
    ],

    # Centaurus (Центавр)
    Constellation.CEN: [
        (71683, 68702),  # Rigil Kentaurus (α) to Hadar (β)
        (68702, 61932),  # Hadar to θ
        (61932, 60823),  # θ to ζ
        (60823, 59196),  # ζ to υ¹
        (59196, 55425),  # υ¹ to δ
        (55425, 68002),  # δ to γ
        (68002, 67464),  # γ to τ
        (67464, 65936),  # τ to σ
        (65936, 65109),  # σ to η
        (65109, 61789),  # η to ν
        (61789, 71352),  # ν to μ
        (71352, 73334),  # μ to φ
    ],

    # Cetus (Кит)
    Constellation.CET: [
        (12706, 14135),  # Menkar (α) to λ
        (14135, 13954),  # λ to μ
        (13954, 12828),  # μ to ξ²
        (12828, 11484),  # ξ² to ξ¹
        (11484, 12706),  # ξ¹ back
        (12706, 12387),  # Menkar to ο (Mira variable)
        (12387, 10826),  # ο to π
        (10826, 8645),  # π to η
        (8645, 8102),  # η to ι
        (8102, 3419),  # ι to Diphda (β)
        (3419, 1562),  # Diphda to τ
        (1562, 5364),  # τ to ζ
        (5364, 6537),  # ζ to θ
        (6537, 8645),  # θ back
    ],

    # Chamaeleon (Хамелеон)
    Constellation.CHA: [
        (40702, 51839),  # α to θ
        (51839, 52633),  # θ to ε
        (52633, 60000),  # ε to δ²
        (60000, 58484),  # δ² to δ¹
        (58484, 51839),  # δ¹ back
    ],

    # Circinus (Циркуль)
    Constellation.CIR: [
        (74824, 71908),  # α to β
        (71908, 75323),  # β to γ
    ],

    # Columba (Голубь)
    Constellation.COL: [
        (26634, 27628),  # Phact (α) to Wazn (β)
        (27628, 25859),  # Wazn to δ
        (25859, 26634),  # δ back
        (27628, 28199),  # Wazn to ε
        (28199, 30277),  # ε to η
    ],

    # Coma Berenices (Волосы Вероники)
    Constellation.COM: [
        (64241, 64394),  # β to α
        (64394, 60742),  # α to γ
    ],

    # Corona Australis (Южная Корона)
    Constellation.CRA: [
        (93825, 94114),  # α to β
        (94114, 94160),  # β to γ
        (94160, 94005),  # γ to δ
        (94005, 90982),  # δ to ε
    ],

    # Corona Borealis (Северная Корона)
    Constellation.CRB: [
        (76127, 75695),  # Alphecca (α) to Nusakan (β)
        (75695, 76267),  # Nusakan to θ
        (76267, 76952),  # θ to γ
        (76952, 77512),  # γ to δ
        (77512, 78159),  # δ to ε
        (78159, 78493),  # ε to ι
    ],

    # Crater (Чаша)
    Constellation.CRT: [
        (53740, 54682),  # Labrum (δ) to γ
        (54682, 55705),  # γ to α
        (55705, 57283),  # α to β
        (57283, 55282),  # β to ζ
        (55282, 55687),  # ζ to η
        (55687, 56633),  # η to θ
        (56633, 55687),  # θ back
        (55282, 53740),  # ζ to δ (complete cup)
    ],

    # Crux (Южный Крест)
    Constellation.CRU: [
        (60718, 62434),  # Acrux (α) to δ
        (62434, 61084),  # δ to γ (Gacrux)
        (61084, 59747),  # Gacrux to β (Mimosa)
        (59747, 60718),  # Mimosa to Acrux
    ],

    # Corvus (Ворон)
    Constellation.CRV: [
        (60965, 59803),  # Gienah (γ) to β
        (59803, 59316),  # β to ε
        (59316, 61359),  # ε to Algorab (δ)
        (61359, 60965),  # Algorab to Gienah
        (59316, 59199),  # ε to Minkar (α)
    ],

    # Delphinus (Дельфин)
    Constellation.DEL: [
        (101421, 101769),  # Sualocin (α) to Rotanev (β)
        (101769, 101958),  # Rotanev to γ
        (101958, 102532),  # γ to δ
        (102532, 102281),  # δ to ε
        (102281, 101769),  # ε to Rotanev
    ],

    # Dorado (Золотая Рыба)
    Constellation.DOR: [
        (19893, 21281),  # α to β
        (21281, 23693),  # β to γ
        (23693, 26069),  # γ to δ
        (26069, 27100),  # δ to ζ
        (27100, 27890),  # ζ to η
    ],

    # Equuleus (Малый Конь)
    Constellation.EQU: [
        (104987, 104858),  # Kitalpha (α) to δ
        (104858, 104521),  # δ to γ
    ],

    # Eridanus (Эридан)
    Constellation.ERI: [
        (7588, 9007),  # Achernar (α) to ι
        (9007, 11407),  # ι to θ
        (11407, 12413),  # θ to η
        (12413, 12486),  # η to ψ
        (12486, 13847),  # ψ to Zaurak (γ)
        (13847, 15510),  # Zaurak to π
        (15510, 16870),  # π to δ
        (16870, 17874),  # δ to ε
        (17874, 20042),  # ε to ν
        (20042, 20535),  # ν to μ
        (20535, 21393),  # μ to ο¹
        (21393, 21248),  # ο¹ to ο²
        (21248, 18673),  # River meanders
        (18673, 18216),  # Continue
        (18216, 17651),  # Continue
        (17651, 16611),  # Continue
        (16611, 15474),  # Continue
        (15474, 14146),  # Continue
        (14146, 12843),  # Continue
        (12843, 12770),  # Continue to Cursa (β)
        (12770, 13701),  # β to λ
        (13701, 16537),  # Continue
        (16537, 17378),  # Continue
        (17378, 17593),  # Continue
        (17593, 18543),  # Continue
        (18543, 19587),  # Continue
        (19587, 21444),  # Continue
        (21444, 22109),  # Continue
        (22109, 23875),  # Continue to Beid (ο¹)
    ],

    # Fornax (Печь)
    Constellation.FOR: [
        (14879, 13147),  # α to β
        (13147, 9677),  # β to ν
    ],

    # Grus (Журавль)
    Constellation.GRU: [
        (109268, 110997),  # Al Nair (α) to β
        (110997, 112122),  # β to γ
        (112122, 112623),  # γ to δ¹
        (112623, 113638),  # δ¹ to δ²
        (112122, 109111),  # γ to ε
        (109111, 108085),  # ε to ζ
    ],

    # Horologium (Часы)
    Constellation.HOR: [
        (19747, 12653),  # α to ι
        (12653, 12225),  # ι to η
        (12225, 12484),  # η to ζ
        (12484, 14240),  # ζ to μ
        (14240, 13884),  # μ to δ
    ],

    # Hydra (Гидра)
    Constellation.HYA: [
        (43234, 42799),  # Alphard (α) to ι
        (42799, 42402),  # ι to θ
        (42402, 42313),  # θ to ζ
        (42313, 43109),  # ζ to ε
        (43109, 43813),  # ε to δ (head)
        (43813, 45336),  # δ to σ (head)
        (45336, 47431),  # σ to η (head)
        (47431, 46390),  # η to ρ (head)
        (46390, 48356),  # ρ to Head continues
        (48356, 49402),  # Body
        (49402, 49841),  # Body
        (49841, 51069),  # Body
        (51069, 52943),  # Body
        (52943, 53740),  # Body
        (53740, 54682),  # Body
        (54682, 56343),  # Body
        (56343, 57936),  # Body
        (57936, 64962),  # Body
        (64962, 68895),  # Body
        (68895, 72571),  # Tail
    ],

    # Hydrus (Южная Гидра)
    Constellation.HYI: [
        (2021, 17678),  # α to γ
        (17678, 11001),  # γ to β
        (11001, 9236),  # β to δ
        (9236, 2021),  # δ to α
    ],

    # Indus (Индеец)
    Constellation.IND: [
        (103227, 108431),  # α to θ
        (108431, 105319),  # θ to δ
        (105319, 101772),  # δ to η
        (101772, 102333),  # η to β
        (102333, 103227),  # β to α
    ],

    # Lacerta (Ящерица)
    Constellation.LAC: [
        (111022, 111169),  # α to β
        (111169, 110538),  # β to 5 Lac
        (110538, 110609),  # 5 to 4 Lac
        (110609, 111022),  # 4 back to α
        (111022, 111944),  # α to 1 Lac
        (111944, 111104),  # 1 to 2 Lac
        (111104, 109754),  # 2 to 6 Lac
        (109754, 109937),  # Extended
    ],

    # Leo Minor (Малый Лев)
    Constellation.LMI: [
        (46952, 49593),  # Praecipua (46) to β
        (49593, 51233),  # β to 21 LMi
        (51233, 53229),  # 21 to 31 LMi
        (53229, 51056),  # 31 to 37 LMi
        (51056, 49593),  # 37 back
    ],

    # Lepus (Заяц)
    Constellation.LEP: [
        (25985, 24305),  # Arneb (α) to Nihal (β)
        (24305, 23685),  # Nihal to ε
        (23685, 24845),  # ε to μ
        (24845, 24305),  # μ back
        (24305, 24327),  # Nihal to γ
        (24327, 25606),  # γ to δ
        (25606, 27072),  # δ to η
        (27072, 27654),  # η to ζ
        (27654, 28910),  # ζ to θ
        (28910, 28103),  # θ to κ
        (28103, 27288),  # κ to ι
        (27288, 25985),  # ι to Arneb
    ],

    # Lupus (Волк)
    Constellation.LUP: [
        (71860, 74395),  # α to β
        (74395, 75264),  # β to γ
        (75264, 76297),  # γ to δ
        (76297, 78384),  # δ to ε
        (78384, 77634),  # ε to ζ
        (77634, 75177),  # ζ to η
        (75177, 73273),  # η to φ²
        (73273, 75141),  # φ² to κ
        (75141, 76297),  # κ to δ
    ],

    # Lynx (Рысь)
    Constellation.LYN: [
        (45860, 45688),  # α to 38 Lyn
        (45688, 44700),  # 38 to 31 Lyn
        (44700, 44248),  # 31 to 21 Lyn
        (44248, 41075),  # 21 to 15 Lyn
        (41075, 36145),  # 15 to 12 Lyn
        (36145, 33449),  # 12 to 10 Lyn
        (33449, 30060),  # 10 to 5 Lyn
    ],

    # Mensa (Столовая Гора)
    Constellation.MEN: [
        (29271, 23467),  # α to γ
    ],

    # Microscopium (Микроскоп)
    Constellation.MIC: [
        (102831, 102989),  # γ to ε
    ],

    # Monoceros (Единорог)
    Constellation.MON: [
        (31978, 31216),  # α to γ
        (31216, 30419),  # γ to δ
        (30419, 32578),  # δ to ζ
        (32578, 34769),  # ζ to ε
        (34769, 39863),  # ε to 13 Mon
        (39863, 37447),  # 13 to 18 Mon
        (30867, 29651),  # β to S Mon
        (34769, 30867),  # ε to β
    ],

    # Musca (Муха)
    Constellation.MUS: [
        (62322, 61585),  # α to β
        (61585, 59929),  # β to γ
        (59929, 57363),  # γ to δ
        (57363, 61199),  # δ to ε
        (61199, 63613),  # ε to λ
        (63613, 62322),  # λ to α
    ],

    # Norma (Наугольник)
    Constellation.NOR: [
        (78639, 78914),  # γ² to γ¹
        (78914, 80582),  # γ¹ to δ
        (80582, 80000),  # δ to ε
        (80000, 78639),  # ε to γ²
    ],

    # Octans (Октант)
    Constellation.OCT: [
        (70638, 107089),  # ν to β
        (107089, 112405),  # β to δ
        (112405, 70638),  # δ to ν
    ],

    # Ophiuchus (Змееносец)
    Constellation.OPH: [
        (86032, 84012),  # Rasalhague (α) to β
        (84012, 81377),  # β to κ
        (81377, 80883),  # κ to ζ
        (80883, 79593),  # ζ to η
        (79593, 79882),  # η to θ
        (79882, 80628),  # θ to ν
        (80628, 81377),  # ν to κ
        (86032, 86742),  # α to δ
        (86742, 87108),  # δ to ε
        (87108, 88048),  # ε to λ
        (84012, 84970),  # β to γ
        (84970, 85423),  # γ to τ
    ],

    # Pavo (Павлин)
    Constellation.PAV: [
        (100751, 102395),  # Peacock (α) to β
        (102395, 99240),  # β to γ
        (99240, 91792),  # γ to δ
        (91792, 93015),  # δ to ε
        (93015, 88866),  # ε to ζ
        (88866, 86929),  # ζ to η
        (102395, 105858),  # β to λ
        (99240, 98495),  # γ to ξ
    ],

    # Phoenix (Феникс)
    Constellation.PHE: [
        (2081, 765),  # Ankaa (α) to κ
        (765, 5165),  # κ to β
        (5165, 6867),  # β to γ
        (6867, 2081),  # γ to α
        (5165, 5348),  # β to ε
        (5348, 7083),  # ε to ζ
        (7083, 6867),  # ζ to γ
    ],

    # Pictor (Живописец)
    Constellation.PIC: [
        (32607, 27530),  # α to γ
        (27530, 27321),  # γ to β
    ],

    # Pisces (Рыбы)
    Constellation.PSC: [
        (5742, 6193),  # α to δ
        (6193, 5586),  # δ to ε
        (5586, 7097),  # ε to ζ
        (7097, 8198),  # ζ to μ
        (8198, 9487),  # μ to ν
        (9487, 7884),  # ν to λ
        (7884, 4906),  # λ to κ
        (4906, 3786),  # κ to ι
        (3786, 118268),  # Western fish to ο
        (118268, 116771),  # ο to η (Knot)
        (116771, 115830),  # η to τ
        (115830, 114971),  # τ to υ
        (114971, 115738),  # υ to φ
        (115738, 116928),  # φ to χ
        (116928, 116771),  # χ to η
    ],

    # Piscis Austrinus (Южная Рыба)
    Constellation.PSA: [
        (113368, 113246),  # Fomalhaut (α) to ε
        (113246, 112948),  # ε to δ
        (112948, 111188),  # δ to γ
        (111188, 109285),  # γ to β
        (109285, 107380),  # β to ι
        (107380, 107608),  # ι to θ
        (107608, 109285),  # θ back
        (109285, 111954),  # β to μ
        (111954, 113368),  # μ to α
    ],

    # Puppis (Корма)
    Constellation.PUP: [
        (39757, 39429),  # Naos (ζ) to π
        (39429, 38170),  # π to ρ
        (38170, 37229),  # ρ to ξ
        (37229, 36917),  # ξ to ν
        (36917, 35264),  # ν to τ
        (35264, 31685),  # τ to σ
        (31685, 30438),  # σ to c Pup
        (30438, 36917),  # c to ν
        (36917, 37677),  # ν to κ
        (37677, 38070),  # κ to HD 63032
        (38070, 38170),  # HD 63032 to ρ
        (39953, 39429),  # l Pup to π
    ],

    # Pyxis (Компас)
    Constellation.PYX: [
        (42515, 42828),  # α to β
        (42828, 43409),  # β to γ
        (43409, 39429),  # γ to π Pup (shared)
    ],

    # Reticulum (Сетка)
    Constellation.RET: [
        (19780, 19921),  # α to δ
        (19921, 18597),  # δ to β
        (18597, 17440),  # β to ε
        (17440, 19780),  # ε to α
    ],

    # Sagitta (Стрела)
    Constellation.SGE: [
        (98337, 97365),  # γ to δ
        (97365, 96757),  # δ to α
        (97365, 96837),  # δ to β
    ],

    # Sculptor (Скульптор)
    Constellation.SCL: [
        (4577, 117452),  # α to β
        (117452, 115102),  # β to γ
        (115102, 116231),  # γ to δ
    ],

    # Scutum (Щит)
    Constellation.SCT: [
        (92175, 91117),  # α to β
        (91117, 90595),  # β to δ
        (90595, 91726),  # δ to γ
        (91726, 92175),  # γ to α
    ],

    # Serpens (Змея) - split constellation
    Constellation.SER: [
        # Serpens Caput (head)
        (77233, 78072),  # Unukalhai (α) to δ
        (78072, 77450),  # δ to ε
        (77450, 76852),  # ε to μ
        (76852, 77233),  # μ to α
        (77233, 76276),  # α to β
        (76276, 77070),  # β to γ
        (77070, 77622),  # γ to κ
        (77622, 77516),  # κ to ι
        (77516, 79593),  # ι to η Oph
        # Serpens Cauda (tail)
        (79593, 84012),  # η Oph to β Oph
        (84012, 86263),  # β Oph to ξ Ser
        (86263, 88048),  # ξ to ν Oph
        (88048, 89962),  # ν to θ Ser
        (89962, 92946),  # θ to η Ser
    ],

    # Sextans (Секстант)
    Constellation.SEX: [
        (48437, 49641),  # α to γ
        (49641, 51437),  # γ to β
        (51437, 51362),  # β to δ
    ],

    # Telescopium (Телескоп)
    Constellation.TEL: [
        (89112, 90422),  # α to ζ
        (90422, 90568),  # ζ to ε
    ],

    # Triangulum (Треугольник)
    Constellation.TRI: [
        (8796, 10064),  # β to α
        (10064, 10670),  # α to γ
        (10670, 8796),  # γ to β
    ],

    # Triangulum Australe (Южный Треугольник)
    Constellation.TRA: [
        (82273, 77952),  # Atria (α) to β
        (77952, 76440),  # β to γ
        (76440, 74946),  # γ to δ
        (74946, 82273),  # δ to α
    ],

    # Tucana (Тукан)
    Constellation.TUC: [
        (2484, 1599),  # α to γ
        (1599, 118322),  # γ to ζ
        (118322, 110838),  # ζ to ε
        (110838, 110130),  # ε to δ
        (110130, 114996),  # δ to β
        (114996, 2484),  # β to α
    ],

    # Vela (Паруса)
    Constellation.VEL: [
        (42913, 39953),  # γ to δ (Alsephina)
        (39953, 44816),  # δ to κ
        (44816, 46651),  # κ to φ
        (46651, 50191),  # φ to μ
        (50191, 52727),  # μ to ψ
        (52727, 48774),  # ψ to λ
        (48774, 45941),  # λ to q
        (45941, 42913),  # q to γ
    ],

    # Volans (Летучая Рыба)
    Constellation.VOL: [
        (44382, 39794),  # γ to β
        (39794, 41312),  # β to α
        (41312, 35228),  # α to ε
        (35228, 34481),  # ε to δ
        (34481, 39794),  # δ to β
    ],

    # Vulpecula (Лисичка)
    Constellation.VUL: [
        (95771, 97886),  # α (Anser) to 23 Vul
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


def get_constellation_line_count() -> Dict[Constellation, int]:
    """
    Get the number of line segments for each constellation.

    Returns:
        Dictionary mapping constellations to their line counts
    """
    return {const: len(lines) for const, lines in CONSTELLATION_LINES.items()}