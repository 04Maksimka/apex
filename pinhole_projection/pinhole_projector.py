"""Module with pinhole projector."""
from dataclasses import dataclass
from datetime import datetime

from numpy.typing import NDArray


@dataclass
class ShotConditions(object):
    """Class of the shot conditions."""
    center_dir: NDArray # можно сделать отдельный ECI data_type
    tilt_angle: float # degrees


@dataclass
class CameraCfg(object):
    """Camera configurations."""
    wight: int    #pix
    height: int   #pix
    foc_len: int  #pix

@dataclass
class Pinhole(object):
    shot_cond: ShotConditions
    camera_cfg: CameraCfg
    time: datetime

    def project(self):
        stars = self.get_stars()
        planets = self.get_planets()
        raise NotImplemented

    def get_stars(self):
        raise NotImplemented

    def get_planets(self):
        #TODO: implement Planets Catalog and to get data from it by time
        raise NotImplemented
