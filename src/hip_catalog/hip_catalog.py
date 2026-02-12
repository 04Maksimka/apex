"""Implementation of Hipparchus catalog."""
from dataclasses import dataclass
from numpy.typing import NDArray
import numpy as np
import pathlib
import hashlib
import json
from typing import Dict, Optional, Any


@dataclass
class CatalogConstraints(object):
    """
    Data class of user Hipparchus catalog constraints.
    """

    max_magnitude: float = 6.0                      # maximum magnitude of stars (dimmest)
    min_magnitude: Optional[float] = None           # minimum magnitude of stars (brightest)

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to a dictionary for caching"""

        return {
            'max_magnitude': self.max_magnitude,
            'min_magnitude': self.min_magnitude,
        }


class Catalog(object):
    """
    Hipparchus catalog optimized for fast numpy operating.
    """

    catalog_name: str                           # catalog filename
    catalog_path: pathlib.Path                  # path to the catalog with catalog_name
    cache_dir: Optional[pathlib.Path]           # cache directory
    use_cache: bool                             # enable / disable caching

    _data: Optional[np.ndarray]                 # catalog data storage
    _constraints: Optional[CatalogConstraints]  # constrains
    _cache_key: Optional[str]                   # key for cache with chosen constrains

    STAR_DTYPE = np.dtype([
        ('v_mag', np.float32),      # visual magnitude, m
        ('ra', np.float32),         # right ascension, rad
        ('dec', np.float32),        # declination, rad
        ('x', np.float32),          # ECI x coordinate
        ('y', np.float32),          # ECI y coordinate
        ('z', np.float32),          # ECI z coordinate
        ('hip_id', np.int32),       # hip identifier
    ])

    def __init__(self, catalog_name: str, cache_dir: Optional[str] = None, use_cache: bool = False):
        """
        :param catalog_name: file star catalog name
        :param cache_dir: caching directory
        :param use_cache: flag enable/disable caching
        """

        self.catalog_name = catalog_name
        self.catalog_path = pathlib.Path(__file__).parent.absolute() / self.catalog_name

        # Make pathlib object for cache directory if not exist
        self.use_cache = use_cache
        if use_cache:
            if cache_dir is None:
                self.cache_dir = pathlib.Path(__file__).parent.absolute() / 'cache'
            else:
                self.cache_dir = pathlib.Path(cache_dir)
            # Create directory, if exists do nothing
            self.cache_dir.mkdir(exist_ok=True)

        # internal storage
        self._data = None
        self._cache_key = None
        self._constraints = None
    #FIXME:
    def _find_cache_root(self) -> pathlib.Path:
        """
        Search for cache directory
        :param project_name: Имя корневой папки проекта
        :param start_path: Начальная точка поиска (по умолчанию - текущий файл)
        :return: Абсолютный путь к корню проекта
        """
        if start_path is None:
            start_path = pathlib.Path(__file__).resolve()
        else:
            start_path = pathlib.Path(start_path).resolve()

        for parent in start_path.parents:
            if parent.name == project_name:
                return parent

        # Если не нашли - падаем с понятной ошибкой
        raise FileNotFoundError(
            f"Project directory '{project_name}' not found in path hierarchy. "
            f"Search started from: {start_path}"
        )

    @staticmethod
    def _generate_cache_key(constraints: CatalogConstraints) -> str:
        """
        Unique cache key generator for chosen catalog constraints.

        :param constraints: catalog constraints
        :return: sha256 key string
        """

        hash_data = {
            'constraints':  constraints.to_dict()
        }
        hash_json = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_json.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> pathlib.Path:
        """ Get path to the cache file by cache key. """
        return self.cache_dir / f"{cache_key}.npy"

    def _get_metadata_path(self, cache_key: str) -> pathlib.Path:
        """ Get path to the metadata by cache key. """
        return self.cache_dir / f"{cache_key}_meta.npy"

    def _is_cached(self, constraints: CatalogConstraints) -> bool:
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

    def load_from_cache(self, constraints: CatalogConstraints) -> NDArray:
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

    def _cache_data(self, data: NDArray, constraints: CatalogConstraints):
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

    @staticmethod
    def _apply_constraints(data: NDArray, constraints: CatalogConstraints) -> NDArray:
        """
        Applies constraints to raw data

        :param data: data to constraint
        :param constraints: constraints
        :return: filtered data
        """

        masks = []

        # Magnitude filtering
        if constraints.min_magnitude is not None:
            mask_mag = (data['v_mag'] >= constraints.min_magnitude) & (data['v_mag'] <= constraints.max_magnitude)
            masks.append(mask_mag)
        else:
            mask_mag = (data['v_mag'] <= constraints.max_magnitude)
            masks.append(mask_mag)

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

        ra = np.deg2rad(raw_data['_RAJ2000'].astype(np.float32))
        dec = np.deg2rad(raw_data['_DEJ2000'].astype(np.float32))
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

    def get_stars(self, constraints: Optional[CatalogConstraints] = None) -> NDArray:
        """
        Main catalog generation method

        :param constraints: constraints, optional, defaults to None
        """
        if constraints is None:
            constraints = CatalogConstraints()

        if self._is_cached(constraints):
            self._data = self.load_from_cache(constraints)
            self._constraints = constraints
            return self._data

        # Load from file
        raw_data = self._load_raw_data()
        # Convert to star type, save state and store to cache
        structured_data = self._convert_to_structured_numpy(raw_data)
        # Apply constraints
        self._data = self._apply_constraints(structured_data, constraints)
        self._constraints = constraints
        self._cache_data(self._data, constraints)

        return self._data

    @property
    def data(self) -> NDArray:
        if self._data is None:
            self.get_stars()
        return self._data

    @property
    def number_of_stars(self) -> int:
        return self._data.shape[0]

    @property
    def constraints(self) -> Optional[CatalogConstraints]:
        return self._constraints

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


def main():
    """Main function."""

    # test catalog print
    catalog = Catalog(catalog_name='hip_data.tsv', use_cache=False)
    constraints = CatalogConstraints(
        max_magnitude=6.0,
    )
    data = catalog.get_stars(constraints=constraints)
    print(data[['x', 'y', 'z']].view('f4'))
    print(data[['x', 'y', 'z']])
    xyz = np.column_stack([data['x'], data['y'], data['z']]).T
    print(xyz[0, :])

if __name__ == "__main__":
    main()