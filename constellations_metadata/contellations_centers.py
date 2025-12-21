from enum import Enum
import numpy as np
from numpy.typing import NDArray
from typing import Dict

class Constellation(Enum):
    AND = "Andromeda"
    ANT = "Antlia"
    APS = "Apus"
    AQR = "Aquarius"
    AQL = "Aquila"
    ARA = "Ara"
    ARI = "Aries"
    AUR = "Auriga"
    BOO = "Boötes"
    CAE = "Caelum"
    CAM = "Camelopardalis"
    CNC = "Cancer"
    CVN = "Canes Venatici"
    CMA = "Canis Major"
    CMI = "Canis Minor"
    CAP = "Capricornus"
    CAR = "Carina"
    CAS = "Cassiopeia"
    CEN = "Centaurus"
    CEP = "Cepheus"
    CET = "Cetus"
    CHA = "Chamaeleon"
    CIR = "Circinus"
    COL = "Columba"
    COM = "Coma Berenices"
    CRA = "Corona Australis"
    CRB = "Corona Borealis"
    CRV = "Corvus"
    CRT = "Crater"
    CRU = "Crux"
    CYG = "Cygnus"
    DEL = "Delphinus"
    DOR = "Dorado"
    DRA = "Draco"
    EQU = "Equuleus"
    ERI = "Eridanus"
    FOR = "Fornax"
    GEM = "Gemini"
    GRU = "Grus"
    HER = "Hercules"
    HOR = "Horologium"
    HYA = "Hydra"
    HYI = "Hydrus"
    IND = "Indus"
    LAC = "Lacerta"
    LEO = "Leo"
    LMI = "Leo Minor"
    LEP = "Lepus"
    LIB = "Libra"
    LUP = "Lupus"
    LYN = "Lynx"
    LYR = "Lyra"
    MEN = "Mensa"
    MIC = "Microscopium"
    MON = "Monoceros"
    MUS = "Musca"
    NOR = "Norma"
    OCT = "Octans"
    OPH = "Ophiuchus"
    ORI = "Orion"
    PAV = "Pavo"
    PEG = "Pegasus"
    PER = "Perseus"
    PHE = "Phoenix"
    PIC = "Pictor"
    PSC = "Pisces"
    PSA = "Piscis Austrinus"
    PUP = "Puppis"
    PYX = "Pyxis"
    RET = "Reticulum"
    SGE = "Sagitta"
    SGR = "Sagittarius"
    SCO = "Scorpius"
    SCL = "Sculptor"
    SCT = "Scutum"
    SER = "Serpens"
    SEX = "Sextans"
    TAU = "Taurus"
    TEL = "Telescopium"
    TRI = "Triangulum"
    TRA = "Triangulum Australe"
    TUC = "Tucana"
    UMA = "Ursa Major"
    UMI = "Ursa Minor"
    VEL = "Vela"
    VIR = "Virgo"
    VOL = "Volans"
    VUL = "Vulpecula"

_centers_array = np.array([
    [0.741033, 0.142421, 0.656191],
    [-0.71918, 0.412782, -0.55892],
    [-0.123317, -0.21627, -0.968514],
    [0.904783, -0.388959, -0.173433],
    [0.407027, -0.911521, 0.058803],
    [-0.107923, -0.580884, -0.8068],
    [0.715424, 0.597657, 0.361905],
    [0.018826, 0.768022, 0.640147],
    [-0.666756, -0.547924, 0.505189],
    [0.245069, 0.735277, -0.631909],
    [-0.008308, 0.389835, 0.920847],
    [-0.597181, 0.72702, 0.338847],
    [-0.725743, -0.244181, 0.643174],
    [-0.216787, 0.894668, -0.390606],
    [-0.406511, 0.907526, 0.10557],
    [0.678128, -0.664458, -0.314066],
    [-0.367404, 0.32372, -0.871906],
    [0.462894, 0.116271, 0.878755],
    [-0.655744, -0.205131, -0.726581],
    [0.341429, -0.096079, 0.934984],
    [0.901463, 0.407263, -0.14663],
    [-0.177373, 0.063552, -0.98209],
    [-0.333473, -0.293221, -0.896],
    [0.01511, 0.811549, -0.584088],
    [-0.906862, -0.161945, 0.38907],
    [0.15327, -0.746949, -0.646975],
    [-0.447759, -0.717842, 0.533118],
    [-0.940023, -0.105717, -0.324316],
    [-0.950983, 0.151117, -0.269807],
    [-0.493487, -0.063691, -0.867418],
    [0.44873, -0.581113, 0.678932],
    [0.626934, -0.743849, 0.231611],
    [0.079563, 0.456461, -0.886179],
    [-0.110914, -0.429646, 0.89616],
    [0.735542, -0.665975, 0.124318],
    [0.505989, 0.800138, -0.32211],
    [0.630344, 0.579715, -0.51633],
    [-0.264685, 0.882474, 0.38882],
    [0.667681, -0.240051, -0.704682],
    [-0.127271, -0.876876, 0.463562],
    [0.399093, 0.441943, -0.803375],
    [-0.892622, 0.342645, -0.292951],
    [0.279072, 0.168347, -0.945399],
    [0.437371, -0.284937, -0.852947],
    [0.65087, -0.256986, 0.714371],
    [-0.910891, 0.335218, 0.240637],
    [-0.757119, 0.358765, 0.545948],
    [0.099872, 0.940354, -0.325206],
    [-0.624491, -0.727535, -0.284085],
    [-0.482759, -0.564656, -0.669408],
    [-0.330517, 0.585975, 0.739859],
    [0.193068, -0.789501, 0.582592],
    [0.039852, 0.212094, -0.976436],
    [0.570281, -0.575028, -0.58662],
    [-0.219899, 0.975109, -0.028401],
    [-0.351169, -0.051908, -0.934872],
    [-0.290553, -0.545111, -0.786405],
    [0.104464, -0.098184, -0.98967],
    [-0.159914, -0.983259, -0.087349],
    [0.099904, 0.992868, 0.06506],
    [0.173279, -0.38805, -0.905202],
    [0.880856, -0.326348, 0.342913],
    [0.449084, 0.552434, 0.702239],
    [0.663788, 0.16161, -0.730252],
    [0.026734, 0.584968, -0.810616],
    [0.968748, 0.158639, 0.190685],
    [0.788629, -0.354769, -0.502198],
    [-0.344443, 0.748873, -0.56617],
    [-0.583976, 0.653906, -0.481019],
    [0.238276, 0.399382, -0.885279],
    [0.402989, -0.857528, 0.319759],
    [0.240998, -0.861463, -0.446992],
    [-0.243419, -0.804129, -0.542332],
    [0.84656, 0.116027, -0.519494],
    [0.166347, -0.971046, -0.171456],
    [-0.346723, -0.934182, 0.084185],
    [-0.902032, 0.428799, -0.049702],
    [0.356509, 0.884427, 0.30115],
    [0.201665, -0.603441, -0.771486],
    [0.705179, 0.464539, 0.535655],
    [-0.198377, -0.356352, -0.91305],
    [0.446086, -0.014441, -0.894874],
    [-0.567625, 0.154885, 0.808586],
    [-0.123038, -0.191253, 0.973799],
    [-0.517672, 0.435727, -0.736314],
    [-0.941525, -0.334105, -0.043644],
    [-0.170357, 0.30691, -0.936368],
    [0.473384, -0.780369, 0.408574],
])

constellation_centers: Dict[Constellation, NDArray] = {
    constellation: _centers_array[i] for i, constellation in enumerate(Constellation)
}

def get_constellation_dir(name: Constellation) -> NDArray:
    """Get center coords in ECI of a constellation.

    :param name: Constellation's Baer name
    """
    return constellation_centers[name]
