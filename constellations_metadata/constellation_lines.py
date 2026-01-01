"""Module containing constellation line data.

This module stores the lines that connect stars to form constellation patterns.
Lines are stored as pairs of HIP (Hipparcos) catalog IDs.

Data source: Based on Stellarium project (GPLv2+) constellation line figures
             https://github.com/Stellarium/stellarium
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
        (54061, 53910), # Dubhe to Merak
        (53910, 58001), # Merak to Phecda
        (58001, 59774), # Phecda to Megrez
        (59774, 62956), # Megrez to Alioth
        (62956, 65378), # Alioth to Mizar
        (65378, 67301), # Mizar to Alkaid
        (59774, 54061), # Megrez to Dubhe (bowl connection)
    ],
    # Ursa Minor (Малая Медведица) - Little Dipper
    Constellation.UMI: [
        (11767, 77055), # Polaris to Yildun
        (77055, 75097), # Yildun to Epsilon UMi
        (75097, 72607), # Epsilon to Zeta UMi
        (72607, 71075), # Zeta to Eta UMi
        (71075, 79822), # Eta to Gamma UMi
        (79822, 82080), # Gamma to Beta UMi
        (82080, 11767), # Beta to Polaris
    ],
    # Orion (Орион)
    Constellation.ORI: [
        (25336, 25930), # Betelgeuse to Bellatrix
        (25930, 26311), # Bellatrix to Alnitak
        (26311, 26727), # Alnitak to Alnilam
        (26727, 26549), # Alnilam to Mintaka
        (26727, 27989), # Alnilam to Saiph
        (27989, 24436), # Saiph to Rigel
        (24436, 26549), # Rigel to Mintaka
        (26311, 25336), # Alnitak to Betelgeuse
    ],
    # Cassiopeia (Кассиопея) - W shape
    Constellation.CAS: [
        (3179, 746), # Caph to Schedar
        (746, 4427), # Schedar to Gamma Cas
        (4427, 6686), # Gamma to Ruchbah
        (6686, 8886), # Ruchbah to Segin
    ],
    # Cygnus (Лебедь) - Northern Cross
    Constellation.CYG: [
        (102098, 100453), # Deneb to Sadr
        (100453, 95947), # Sadr to Gienah
        (100453, 104732), # Sadr to Delta Cyg
        (104732, 97165), # Delta to Albireo
        (100453, 102488), # Sadr to Epsilon Cyg (crossbeam)
    ],
    # Leo (Лев)
    Constellation.LEO: [
        (49669, 50583), # Regulus to Eta Leo
        (50583, 50335), # Eta to Algieba
        (50335, 49583), # Algieba to Adhafera
        (49583, 47908), # Adhafera to Rasalas
        (49669, 54872), # Regulus to Denebola
        (54872, 57632), # Denebola to Zosma
        (57632, 50583), # Zosma to Eta Leo
        (57632, 54879), # Zosma to Chertan
    ],
    # Gemini (Близнецы)
    Constellation.GEM: [
        (36850, 37826), # Castor to Pollux
        (36850, 34088), # Castor to Alhena
        (37826, 35550), # Pollux to Wasat
        (35550, 34088), # Wasat to Alhena
        (36850, 30343), # Castor to Mebsuta
        (37826, 36962), # Pollux to Tejat
    ],
    # Taurus (Телец)
    Constellation.TAU: [
        (21421, 20889), # Aldebaran to Epsilon Tau
        (20889, 20894), # Epsilon to Delta Tau
        (20894, 21881), # Delta to Theta2 Tau
        (21881, 20205), # Theta2 to Gamma Tau
        (20205, 21421), # Gamma to Aldebaran
        (21421, 25428), # Aldebaran to Elnath
    ],
    # Aquila (Орёл)
    Constellation.AQL: [
        (97649, 93747), # Altair to Tarazed
        (93747, 95501), # Tarazed to Deneb el Okab
        (97649, 98036), # Altair to Alshain
        (97649, 93805), # Altair to Delta Aql
    ],
    # Lyra (Лира)
    Constellation.LYR: [
        (91262, 91919), # Vega to Epsilon Lyr
        (91262, 91926), # Vega to Zeta Lyr
        (91926, 92791), # Zeta to Beta Lyr
        (92791, 93194), # Beta to Gamma Lyr
    ],
    # Scorpius (Скорпион)
    Constellation.SCO: [
        (80763, 78820), # Antares to Tau Sco
        (78820, 78265), # Tau to Epsilon Sco
        (78265, 79593), # Epsilon to Delta Sco
        (79593, 81266), # Delta to Beta Sco
        (80763, 80112), # Antares to Sigma Sco
        (80112, 85927), # Sigma to Lambda Sco
        (85927, 86228), # Lambda to Shaula
        (86228, 85696), # Shaula to Lesath
    ],
    # Sagittarius (Стрелец) - Teapot
    Constellation.SGR: [
        (88635, 90185), # Kaus Australis to Kaus Media
        (90185, 89931), # Kaus Media to Kaus Borealis
        (89931, 92855), # Kaus Borealis to Nunki
        (92855, 93506), # Nunki to Tau Sgr
        (93506, 95241), # Tau to Phi Sgr
        (95241, 88635), # Phi to Kaus Australis (complete teapot body)
        (90185, 93864), # Kaus Media to Ascella (handle)
    ],
    # Andromeda (Андромеда)
    Constellation.AND: [
        (677, 3092), # Alpheratz to Mirach
        (3092, 5447), # Mirach to Almach
        (3092, 9640), # Mirach to Delta And
        (9640, 7607), # Delta to Beta And
    ],
    # Perseus (Персей)
    Constellation.PER: [
        (15863, 14328), # Mirfak to Gamma Per
        (14328, 13268), # Gamma to Delta Per
        (13268, 14576), # Delta to Epsilon Per
        (14576, 15863), # Epsilon to Mirfak
        (13847, 14328), # Algol to Gamma Per
    ],
    # Pegasus (Пегас) - Great Square
    Constellation.PEG: [
        (677, 113881), # Alpheratz to Scheat
        (113881, 113963), # Scheat to Markab
        (113963, 112158), # Markab to Algenib
        (112158, 677), # Algenib to Alpheratz
        (113963, 107315), # Markab to Enif
    ],
    # Aquarius (Водолей)
    Constellation.AQR: [
        (110960, 109074), # Sadalsuud to Sadalmelik
        (109074, 106278), # Sadalmelik to Lambda Aqr
        (110960, 111123), # Sadalsuud to Xi Aqr
        (111123, 112961), # Xi to Theta Aqr
        (112961, 113136), # Theta to Delta Aqr
    ],
    # Capricornus (Козерог)
    Constellation.CAP: [
        (100345, 100064), # Prima Giedi to Secunda Giedi
        (100064, 102978), # Secunda to Dabih
        (102978, 105881), # Dabih to Nashira
        (105881, 107556), # Nashira to Deneb Algedi
        (107556, 106985), # Deneb to Omega Cap
    ],
    # Aries (Овен)
    Constellation.ARI: [
        (8903, 9884), # Hamal to Sheratan
        (9884, 8832), # Sheratan to Mesarthim
        (8903, 13209), # Hamal to 41 Ari
    ],
    # Cancer (Рак)
    Constellation.CNC: [
        (42911, 43103), # Acubens to Asellus Borealis
        (43103, 42806), # Asellus Borealis to Asellus Australis
        (42806, 40526), # Asellus Australis to Beta Cnc
    ],
    # Virgo (Дева)
    Constellation.VIR: [
        (65474, 63608), # Spica to Porrima
        (63608, 60129), # Porrima to Vindemiatrix
        (60129, 57757), # Vindemiatrix to Delta Vir
        (57757, 63090), # Delta to Zavijava
        (63090, 65474), # Zavijava to Spica
    ],
    # Libra (Весы)
    Constellation.LIB: [
        (74785, 72622), # Zubenelgenubi to Zubeneschamali
        (72622, 76333), # Zubeneschamali to Sigma Lib
        (76333, 74785), # Sigma to Zubenelgenubi
    ],
    # Draco (Дракон)
    Constellation.DRA: [
        (87833, 85670), # Thuban to Edasich
        (85670, 83895), # Edasich to Aldhibah
        (83895, 80331), # Aldhibah to Altais
        (80331, 78527), # Altais to Chi Dra
        (78527, 75458), # Chi to Grumium
        (75458, 68756), # Grumium to Eltanin
        (68756, 61281), # Eltanin to Rastaban
        (61281, 56211), # Rastaban to Kuma
    ],
    # Auriga (Возничий)
    Constellation.AUR: [
        (24608, 25428), # Capella to Menkalinan
        (25428, 28360), # Menkalinan to Theta Aur
        (28360, 23015), # Theta to Hassaleh
        (23015, 24608), # Hassaleh to Capella
        (24608, 28380), # Capella to Epsilon Aur
    ],
    # Bootes (Волопас)
    Constellation.BOO: [
        (69673, 71075), # Arcturus to Muphrid
        (69673, 67927), # Arcturus to Seginus
        (67927, 69483), # Seginis to Izar
        (69483, 69673), # Izar to Arcturus
        (71075, 72105), # Muphrid to Nekkar
    ],
    # Cepheus (Цефей)
    Constellation.CEP: [
        (105199, 106032), # Alderamin to Alfirk
        (106032, 108917), # Alfirk to Errai
        (108917, 109857), # Errai to Alrai
        (109857, 116727), # Alrai to Erakis
        (116727, 105199), # Erakis to Alderamin
    ],
    # Hercules (Геркулес)
    Constellation.HER: [
        (84345, 85693), # Rasalgethi to Kornephoros
        (85693, 81693), # Kornephoros to Zeta Her
        (81693, 80816), # Zeta to Pi Her
        (80816, 84345), # Pi to Rasalgethi
        (85693, 86974), # Kornephoros to Sarin
        (86974, 87808), # Sarin to Eta Her
    ],
    Constellation.ANT: [
        (53502, 51172), (51172, 46515)
    ],
    Constellation.APS: [
        (72370, 81065), (81065, 80047), (80047, 81852), (81852, 81065)
    ],
    Constellation.CAE: [
        (23595, 21861), (21861, 21770), (21770, 21060)
    ],
    Constellation.CAM: [
        (23040, 23522), (23522, 22783), (22783, 29997), (29997, 33694), (33694, 29997),
        (29997, 22783), (22783, 17959), (17959, 17884), (17884, 16228)
    ],
    Constellation.CVN: [
        (63125, 61317)
    ],
    Constellation.CMA: [
        (30324, 32349), (32349, 34444), (34444, 33579), (33579, 34444), (34444, 35904),
        (35904, 30324), (30324, 31592), (31592, 33152), (33152, 33579), (33579, 32349),
        (32349, 33347), (33347, 34045), (34045, 33160), (33160, 33347)
    ],
    Constellation.CMI: [
        (37279, 36188)
    ],
    Constellation.CAR: [
        (30438, 45238), (45238, 50099), (50099, 52419), (52419, 51576), (51576, 50371),
        (50371, 45556), (45556, 42913), (42913, 51576), (51576, 53253), (53253, 52419),
        (52419, 54301), (54301, 54751), (54751, 54463), (54463, 53253), (53253, 45556),
        (45556, 41037), (41037, 38827), (38827, 39953)
    ],
    Constellation.CEN: [
        (61932, 66657), (66657, 68702), (68702, 71683), (71683, 68702), (68702, 66657),
        (66657, 68002), (68002, 61932), (61932, 68002), (68002, 68282), (68282, 68245),
        (68245, 71352), (71352, 68245), (68245, 68862), (68862, 70090), (70090, 68933),
        (68933, 67464), (67464, 68002), (68002, 55425), (55425, 59196), (59196, 60823),
        (60823, 61932), (61932, 60823), (60823, 59449), (59449, 56243), (56243, 67464),
        (67464, 65936), (65936, 65109), (65109, 61789), (61789, 71352), (71352, 73334)
    ],
    Constellation.CET: [
        (12706, 14135), (14135, 13954), (13954, 12828), (12828, 11484), (11484, 12706),
        (12706, 12387), (12387, 10826), (10826, 8645), (8645, 8102), (8102, 3419),
        (3419, 1562), (1562, 5364), (5364, 6537), (6537, 8645)
    ],
    Constellation.CHA: [
        (40702, 51839), (51839, 52633), (52633, 60000), (60000, 58484), (58484, 51839)
    ],
    Constellation.CIR: [
        (74824, 71908), (71908, 75323)
    ],
    Constellation.COL: [
        (26634, 27628), (27628, 25859), (25859, 26634), (26634, 28328), (28328, 27628),
        (27628, 28199), (28199, 30277)
    ],
    Constellation.COM: [
        (64241, 64241), (64241, 64394), (64394, 60742)
    ],
    Constellation.CRA: [
        (93825, 94114), (94114, 94160), (94160, 94005), (94005, 90982)
    ],
    Constellation.CRB: [
        (76127, 75695), (75695, 76267), (76267, 76952), (76952, 77512), (77512, 78159),
        (78159, 78493)
    ],
    Constellation.CRT: [
        (53740, 54682), (54682, 55705), (55705, 57283), (57283, 58188), (58188, 57283),
        (57283, 55705), (55705, 55282), (55282, 55687), (55687, 56633), (56633, 55687),
        (55687, 55282), (55282, 53740)
    ],
    Constellation.CRU: [
        (60718, 61084), (61084, 62434), (62434, 59747)
    ],
    Constellation.CRV: [
        (60965, 59803), (59803, 59316), (59316, 61359), (61359, 60965), (60965, 59316),
        (59316, 59199)
    ],
    Constellation.DEL: [
        (101421, 101769), (101769, 101958), (101958, 102532), (102532, 102281),
        (102281, 101769)
    ],
    Constellation.DOR: [
        (19893, 21281), (21281, 23693), (23693, 26069), (26069, 21281), (21281, 26069),
        (26069, 27100), (27100, 27890), (27890, 26069)
    ],
    Constellation.EQU: [
        (104987, 104858), (104858, 104521)
    ],
    Constellation.ERI: [
        (23875, 22109), (22109, 21444), (21444, 19587), (19587, 18543), (18543, 17593),
        (17593, 17378), (17378, 16537), (16537, 13701), (13701, 12770), (12770, 12843),
        (12843, 14146), (14146, 15474), (15474, 16611), (16611, 17651), (17651, 18216),
        (18216, 18673), (18673, 21248), (21248, 21393), (21393, 20535), (20535, 20042),
        (20042, 17874), (17874, 16870), (16870, 15510), (15510, 13847), (13847, 12486),
        (12486, 12413), (12413, 11407), (11407, 9007), (9007, 7588)
    ],
    Constellation.FOR: [
        (14879, 13147), (13147, 9677)
    ],
    Constellation.GRU: [
        (108085, 109111), (109111, 110997), (110997, 109268), (109268, 112122), (112122, 110997),
        (110997, 112122), (112122, 112623), (112623, 113638)
    ],
    Constellation.IND: [
        (103227, 102333), (102333, 101772), (101772, 105319), (105319, 108431), (108431, 103227)
    ],
    Constellation.LMI: [
        (46952, 49593), (49593, 51233), (51233, 53229), (53229, 51056), (51056, 49593)
    ],
    Constellation.MEN: [
        (29271, 23467)
    ],
    Constellation.MIC: [
        (102831, 102989)
    ],
    Constellation.MON: [
        (31978, 31216), (31216, 30419), (30419, 32578), (32578, 31216), (31216, 32578),
        (32578, 34769), (34769, 30867), (30867, 29651), (29651, 30867), (30867, 34769),
        (34769, 39863), (39863, 37447)
    ],
    Constellation.MUS: [
        (57363, 59929), (59929, 61585), (61585, 62322), (62322, 63613), (63613, 61199), (61199, 61585)
    ],
    Constellation.NOR: [
        (78639, 80000), (80000, 80582), (80582, 78914), (78914, 78639)
    ],
    Constellation.OCT: [
        (70638, 107089), (107089, 112405), (112405, 70638)
    ],
    Constellation.OPH: [
        (86032, 83000), (83000, 80883), (80883, 79593), (79593, 79882), (79882, 80628),
        (80628, 81377), (81377, 80628), (80628, 79882), (79882, 79593), (79593, 80883),
        (80883, 83000), (83000, 81377), (81377, 84012), (84012, 86742), (86742, 87108),
        (87108, 88048), (88048, 87108), (87108, 86742), (86742, 86032), (86032, 84012),
        (84012, 84970), (84970, 85423), (85423, 81377), (81377, 80894), (80894, 80569),
        (80569, 80343), (80343, 80473)
    ],
    Constellation.PAV: [
        (100751, 99240), (99240, 102395), (102395, 100751), (100751, 105858), (105858, 102395),
        (102395, 91792), (91792, 99240), (99240, 98495), (98495, 99240), (99240, 93015),
        (93015, 88866), (88866, 86929), (86929, 88866), (88866, 90098), (90098, 92609), (92609, 99240)
    ],
    Constellation.PHE: [
        (2081, 5165), (5165, 6867), (6867, 2081), (2081, 765), (765, 5165), (5165, 5348),
        (5348, 7083), (7083, 6867)
    ],
    Constellation.PIC: [
        (32607, 27530), (27530, 27321)
    ],
    Constellation.PSA: [
        (113368, 113246), (113246, 112948), (112948, 111188), (111188, 109285), (109285, 107380),
        (107380, 107608), (107608, 109285), (109285, 111954), (111954, 113368)
    ],
    Constellation.SCL: [
        (4577, 117452), (117452, 115102), (115102, 116231)
    ],
    Constellation.SCT: [
        (92175, 91117), (91117, 90595), (90595, 91726), (91726, 92175)
    ],
    Constellation.SER: [
        (77233, 78072), (78072, 77450), (77450, 76852), (76852, 77233), (77233, 76276),
        (76276, 77070), (77070, 77622), (77622, 77516), (77516, 79593), (79593, 84012),
        (84012, 86263), (86263, 88048), (88048, 89962), (89962, 92946)
    ],
    Constellation.SEX: [
        (48437, 49641), (49641, 51437), (51437, 51362)
    ],
    Constellation.SGE: [
        (98337, 97365), (97365, 96757), (96757, 97365), (97365, 96837)
    ],
    Constellation.TEL: [
        (89112, 90422), (90422, 90568)
    ],
    Constellation.TRA: [
        (82273, 77952), (77952, 76440), (76440, 74946), (74946, 82273)
    ],
    Constellation.TRI: [
        (8796, 10064), (10064, 10670), (10670, 8796)
    ],
    Constellation.TUC: [
        (2484, 1599), (1599, 118322), (118322, 110838), (110838, 110130), (110130, 114996), (114996, 2484)
    ],
    Constellation.VEL: [
        (42913, 39953), (39953, 44816), (44816, 46651), (46651, 50191), (50191, 52727),
        (52727, 48774), (48774, 45941), (45941, 42913)
    ],
    Constellation.VUL: [
        (95771, 97886)
    ],
    Constellation.HOR: [
        (19747, 12653), (12653, 12225), (12225, 12484), (12484, 14240), (14240, 13884)
    ],
    Constellation.HYA: [
        (43234, 42799), (42799, 42402), (42402, 42313), (42313, 43109), (43109, 43813),
        (43813, 45336), (45336, 47431), (47431, 46390), (46390, 48356), (48356, 49402),
        (49402, 49841), (49841, 51069), (51069, 52943), (52943, 53740), (53740, 54682),
        (54682, 56343), (56343, 57936), (57936, 64962), (64962, 68895), (68895, 72571)
    ],
    Constellation.HYI: [
        (2021, 17678), (17678, 11001), (11001, 9236), (9236, 2021)
    ],
    Constellation.LAC: [
        (111022, 111169), (111169, 110538), (110538, 110609), (110609, 111022), (111022, 110351),
        (110351, 111104), (111104, 111944), (111944, 111104), (111104, 111944), (111944, 111022),
        (111022, 111944), (111944, 111104), (111104, 109754), (109754, 109937)
    ],
    Constellation.LEP: [
        (23685, 24305), (24305, 25985), (25985, 25606), (25606, 23685), (23685, 24845),
        (24845, 24305), (24305, 24327), (24327, 25606), (25606, 27072), (27072, 27654),
        (27654, 28910), (28910, 28103), (28103, 27288), (27288, 25985)
    ],
    Constellation.LUP: [
        (71860, 74395), (74395, 75264), (75264, 76297), (76297, 75141), (75141, 73273),
        (73273, 75141), (75141, 76297), (76297, 78384), (78384, 75177), (75177, 77634),
        (77634, 78384), (78384, 74395)
    ],
    Constellation.LYN: [
        (45860, 45688), (45688, 44700), (44700, 44248), (44248, 41075), (41075, 36145),
        (36145, 33449), (33449, 30060)
    ],
    Constellation.PUP: [
        (39953, 39429), (39429, 39757), (39757, 38170), (38170, 37229), (37229, 36917),
        (36917, 35264), (35264, 31685), (31685, 30438), (30438, 36917), (36917, 37677),
        (37677, 38070), (38070, 38170)
    ],
    Constellation.PYX: [
        (39429, 42515), (42515, 42828), (42828, 43409)
    ],
    Constellation.RET: [
        (19780, 17440), (17440, 18597), (18597, 19921), (19921, 19780)
    ],
    Constellation.PSC: [
        (5742, 6193), (6193, 5586), (5586, 5742), (5742, 7097), (7097, 8198),
        (8198, 9487), (9487, 7884), (7884, 4906), (4906, 3786), (3786, 118268),
        (118268, 116771), (116771, 115830), (115830, 114971), (114971, 115738), (115738, 116928),
        (116928, 116771)
    ],
    Constellation.VOL: [
        (44382, 41312), (41312, 39794), (39794, 35228), (35228, 34481), (34481, 39794), (39794, 44382)
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