"""Implementation of Hipparchus catalog."""
from dataclasses import dataclass
from numpy.typing import NDArray
import numpy as np
import pathlib
import hashlib
import json
from typing import Dict, Tuple, List, Optional, Any


@dataclass
class Catalogconstraints(object):
    """
    Data class of user Hipparchus catalog constraints.
    """

    max_magnitude: float = 6.0                      # maximum magnitude of stars (dimmest)
    min_magnitude: Optional[float] = None           # minimum magnitude of stars (brightest)
    ra_range: Optional[Tuple[float, float]] = None  # right ascension range
    dec_range: Optional[Tuple[float, float]] = None # declination range

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to a dictionary for caching"""

        return {
            'max_magnitude': self.max_magnitude,
            'min_magnitude': self.min_magnitude,
            'ra_range': self.ra_range,
            'dec_range': self.dec_range,
        }


class NumpyCatalog(object):
    """
    Hipparchus catalog optimized for fast numpy operating.
    """

    catalog_name: str
    catalog_path: pathlib.Path
    cache_dir: pathlib.Path
    use_cache: bool

    _data: Optional[np.ndarray]
    _constraints: Optional[Catalogconstraints]
    _cache_key: Optional[str]

    STAR_DTYPE = np.dtype([
        ('v_mag', np.float32),      # visual magnitude, m
        ('ra', np.float32),         # right ascension, rad
        ('dec', np.float32),        # declination, rad
        ('x', np.float32),          # ECI x coordinate
        ('y', np.float32),          # ECI y coordinate
        ('z', np.float32),          # ECI z coordinate
        ('hip_id', np.int32),       # hip identifier
    ])

    def __init__(self, catalog_name: str, cache_dir: str, use_cache: bool):
        """
        :param catalog_name: file star catalog name
        :param cache_dir: caching directory
        :param use_cache: flag enable/disable caching
        """

        self.catalog_name = catalog_name
        self.catalog_path = pathlib.Path(__file__).parent.absolute() / self.catalog_name

        # make pathlib object for cache directory if not exist
        self.cache_dir = pathlib.Path(cache_dir)
        self.use_cache = use_cache
        self.cache_dir.mkdir(exist_ok=True)

        # internal storage
        self._data = None
        self._cache_key = None
        self._constraints = None

    @staticmethod
    def _generate_cache_key(constraints: Catalogconstraints) -> str:
        """
        Unique cache key generator.

        :param constraints: catalog constraints
        :return: sha256 key string
        """

        hash_data = {
            'constraints':  constraints.to_dict()
        }
        hash_json = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_json.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> pathlib.Path:
        return self.cache_dir / f"{cache_key}.npy"

    def _get_metadata_path(self, cache_key: str) -> pathlib.Path:
        return self.cache_dir / f"{cache_key}_meta.npy"

    def _is_cached(self, constraints: Catalogconstraints) -> bool:
        """
        Checks if catalog with these constraints is cached or not.

        :param constraints: catalog constraints
        """

        if not self.use_cache:
            return False

        cache_key = self._generate_cache_key(constraints)
        cache_file = self._get_cache_path(cache_key)
        meta_file = self._get_metadata_path(cache_key)

        return cache_file.exists() and meta_file.exists()

    def load_from_cache(self, constraints: Catalogconstraints) -> NDArray:
        """
        Loads catalog from cache.

        :param constraints: catalog constraints
        """

        if not self.use_cache:
            raise Exception("Caching disabled.")

        cache_key = self._generate_cache_key(constraints)
        cache_file = self._get_cache_path(cache_key)

        if not self._is_cached(constraints):
            raise FileNotFoundError(f"Cache file {cache_key} not found.")

        data = np.load(cache_file)
        return data

    def cache_data(self, data: NDArray, constraints: Catalogconstraints):
        """
        Store data to cache

        :param data: data to be cached
        :param constraints: constraints
        """

        if not self.use_cache:
            return

        cache_key = self._generate_cache_key(constraints)
        cache_file = self._get_cache_path(cache_key)
        meta_file = self._get_metadata_path(cache_key)

        np.save(cache_file, data)
        metadata = {
            'constraints': constraints.to_dict(),
        }
        np.save(meta_file, metadata)

    def _load_raw_data(self) -> NDArray:
        """
        Loads raw data from file

        :return: cleaned raw data
        """

        raw_data = np.genfromtxt(
            fname=self.catalog_path,
            delimiter=';',
            dtype=None,
            names=True,
            encoding='utf-8',
            missing_values='',
            filling_values=None,
        )

        clean_data = self._clean_raw_data(raw_data)
        return clean_data

    def _apply_constraints(self, data: NDArray, constraints: Catalogconstraints) -> NDArray:
        """
        Applies constraints to raw data

        :param data: data to constraint
        :param constraints: constraints
        :return: constrained data
        """

        masks = []

        # Magnitude filtering
        if constraints.max_magnitude is not None:
            mask_mag = (constraints.min_magnitude <= data['Vmag']) & (data['Vmag'] <= constraints.max_magnitude)
            masks.append(mask_mag)

        # Declination filtering
        if constraints.min_magnitude is not None:
            mask_min_mag = data['Vmag'] >= constraints.min_magnitude
            masks.append(mask_min_mag)

        # Right ascension filtering
        if constraints.ra_range is not None:
            ra_min, ra_max = constraints.ra_range
            mask_ra = (data['_RAJ2000'] >= ra_min) & (data['_RAJ2000'] <= ra_max)
            masks.append(mask_ra)

        # Declination filtering
        if constraints.dec_range is not None:
            dec_min, dec_max = constraints.dec_range
            mask_dec = (data['_DEJ2000'] >= dec_min) & (data['_DEJ2000'] <= dec_max)
            masks.append(mask_dec)

        # Combine all the masks
        if masks:
            combined_mask = np.all(masks, axis=0)
            filtered_data = data[combined_mask]
        else:
            filtered_data = data

        return filtered_data

    def _convert_to_structured_numpy(self, raw_data: NDArray):
        """
        Converts raw data to structured numpy array of STAR_DTYPEs

        :param raw_data: raw data
        """

        number_of_stars = raw_data.shape[0]
        structured_data = np.zeros(number_of_stars, dtype=self.STAR_DTYPE)

        structured_data['v_mag'] = raw_data['Vmag'].astype(np.float32)

        ra = np.deg2rad(raw_data['_RAJ2000'])
        dec = np.deg2rad(raw_data['_DEJ2000'])
        structured_data['ra'] = ra
        structured_data['dec'] = dec

        cos_ra = np.cos(ra)
        sin_ra = np.sin(ra)
        cos_dec = np.cos(dec)
        sin_dec = np.sin(dec)
        structured_data['x'] = (cos_ra * cos_dec).astype(np.float32)
        structured_data['y'] = (sin_ra * cos_dec).astype(np.float32)
        structured_data['z'] = sin_dec.astype(np.float32)

        structured_data['hip_id'] = raw_data['HIP'].astype(np.int32)

        return structured_data

    def get_stars(self, constraints: Optional[Catalogconstraints] = None) -> NDArray:
        """
        Main catalog generation method

        :param constraints: constraints, optional, defaults to None
        """
        if constraints is None:
            constraints = Catalogconstraints()

        if self._is_cached(constraints):
            self._data = self.load_from_cache(constraints)
            self._constraints = constraints
            return self._data

        # Load from file
        raw_data = self._load_raw_data()
        # Apply constraints
        filtered_data = self._apply_constraints(raw_data, constraints)
        # Convert to star type, save state and store to cache
        self._data = self._convert_to_structured_numpy(filtered_data)
        self._constraints = constraints
        self.cache_data(self._data, constraints)

        return self._data

    @property
    def data(self) -> NDArray:
        if self._data is None:
            self.get_stars()
        return self._data

    @staticmethod
    def _clean_raw_data(raw_data):
        """
        Removes units and rows with missing values
        in right ascension and declinations columns

        :param raw_data: source catalog data
        :return: cleaned catalog data
        """
        raw_data = raw_data[1:]
        mask = (raw_data['_RAJ2000'] != '') & (raw_data['_DEJ2000'] != '')
        clean_data = raw_data[mask]

        return clean_data



@dataclass
class EquatorialCoords(object):
    """Data class of equatorial coordinates."""

    right_ascension: float
    declination: float

    def __repr__(self):
        return f'(alpha:{np.rad2deg(self.right_ascension):8.2f}, ' \
               f'delta:{np.rad2deg(self.declination):8.2f})'


@dataclass
class ECICoords(object):
    """Data class of ECI coordinates."""

    x: float
    y: float
    z: float

    def __repr__(self):
        return f'(x: {self.x:6.2f}, y: {self.y:6.2f}, z: {self.z:6.2f})'

    def __iter__(self):
        for att in ['x', 'y', 'z']:
            yield getattr(self, att)


@dataclass
class Star(object):
    """Class of a singular star."""

    v_mag: float                    # visual magnitude
    eq_coords: EquatorialCoords     # equatorial coordinates (alpha, delta)

    def __repr__(self):
        return f'eq={self.eq_coords}, eci={self.eci_coords}, m={self.v_mag:7.2f}'

    @property
    def eci_coords(self) -> ECICoords:
        """Initialize ECI coordinates."""

        # short names for usage
        alpha = self.eq_coords.right_ascension
        delta = self.eq_coords.declination

        # to spherical coordinate system
        x = np.cos(alpha) * np.cos(delta)
        y = np.sin(alpha) * np.cos(delta)
        z = np.sin(delta)

        return ECICoords(x=x, y=y, z=z)


@dataclass
class Catalog(object):
    """
    Hipparchus catalog.
    """

    mag_criteria: float = 5.5
    catalog_name: str = 'hip_data.tsv'

    def parse_data(self) -> NDArray[Star]:
        """
        Returns list of stars with given constraints.
        """

        catalog_path = pathlib.Path(__file__).parent.absolute() / self.catalog_name

        # read data from file
        raw_data = np.genfromtxt(
            fname=catalog_path,
            delimiter=';',
            dtype=None,
            names=True,
            encoding='utf-8',
            missing_values='',
            filling_values=None
        )

        cleaned_data = self._clean_raw_data(raw_data)

        # make numpy array of Stars
        data = np.array(
            [
                Star(
                    v_mag=float(line['Vmag']),
                    eq_coords=EquatorialCoords(
                        right_ascension=np.deg2rad(float(line['_RAJ2000'])),
                        declination=np.deg2rad(float(line['_DEJ2000']))
                    )
                )
                for line in cleaned_data
            ],
            dtype=Star
        )
        return data

    @staticmethod
    def _clean_raw_data(raw_data):
        """
        function removing units and rows with missing values
        in right ascension and declinations columns

        :param raw_data: source catalog data
        :return: cleaned catalog data
        """
        raw_data = raw_data[1:]
        mask = (raw_data['_RAJ2000'] != '') & (raw_data['_DEJ2000'] != '')
        clean_data = raw_data[mask]

        return clean_data


def main():
    """Main function."""

    # test catalog print
    catalog = Catalog()
    data = catalog.parse_data()
    print(data)

if __name__ == "__main__":
    main()