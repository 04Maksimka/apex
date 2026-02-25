"""Implementation of Hipparchus catalog."""

import hashlib
import json
import pathlib
import tempfile
import warnings
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from numpy.typing import NDArray


@dataclass
class CatalogConstraints(object):
    """Data class of user Hipparchus catalog constraints."""

    max_magnitude: float = 6.0  # maximum magnitude of stars (dimmest)
    min_magnitude: Optional[float] = (
        None  # minimum magnitude of stars (brightest)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to a dictionary for caching"""

        return {
            "max_magnitude": self.max_magnitude,
            "min_magnitude": self.min_magnitude,
        }


class Catalog(object):
    """Hipparchus catalog optimized for fast numpy operating."""

    catalog_name: str  # catalog filename
    catalog_path: pathlib.Path  # path to the catalog with catalog_name
    cache_dir: Optional[pathlib.Path]  # cache directory
    use_cache: bool  # enable / disable caching

    _data: Optional[NDArray]  # catalog data storage
    _constraints: Optional[CatalogConstraints]  # constrains
    _cache_key: Optional[str]  # key for cache with chosen constrains

    STAR_DTYPE = np.dtype(
        [
            ("v_mag", np.float32),  # visual magnitude, m
            ("ra", np.float32),  # right ascension, rad
            ("dec", np.float32),  # declination, rad
            ("x", np.float32),  # ECI x coordinate
            ("y", np.float32),  # ECI y coordinate
            ("z", np.float32),  # ECI z coordinate
            ("hip_id", np.int32),  # hip identifier
        ]
    )

    def __init__(
        self,
        catalog_name: str,
        cache_dir: Optional[str] = None,
        use_cache: bool = False,
    ):
        """
        :param catalog_name: file star catalog name
        :type catalog_name: str
        :param cache_dir: caching directory (if None — use
        /tmp/astrageek_cache)
        :type cache_dir: str
        :param use_cache: flag enable/disable caching
        :type use_cache: bool
        """

        self.catalog_name = catalog_name
        self.catalog_path = (
            pathlib.Path(__file__).parent.absolute() / self.catalog_name
        )

        self.use_cache = use_cache
        if use_cache:
            if cache_dir is not None:
                self.cache_dir = pathlib.Path(cache_dir)
            else:
                # Используем /tmp — всегда доступен для записи на любом
                # сервере. В отличие от директории проекта, не требует
                # особых прав.
                self.cache_dir = (
                    pathlib.Path(tempfile.gettempdir()) / "astrageek_cache"
                )

            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                # Если даже /tmp недоступен —
                # отключаем кэш и работаем без него.
                warnings.warn(
                    f"Cannot create cache directory '{self.cache_dir}': {e}. "
                    "Caching disabled — "
                    "catalog will be loaded from file on every request."
                )
                self.use_cache = False

        # internal storage
        self._data = None
        self._cache_key = None
        self._constraints = None

    @staticmethod
    def _generate_cache_key(constraints: CatalogConstraints) -> str:
        """
        Unique cache key generator for chosen catalog constraints.

        :param constraints: catalog constraints
        :type constraints: CatalogConstraints

        :return: sha256 key string
        :rtype: str
        """

        hash_data = {"constraints": constraints.to_dict()}
        hash_json = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_json.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> pathlib.Path:
        """
        Get path to the cache file by cache key.

        :param cache_key: cache key
        :type cache_key: str

        :return: cache path
        :rtype: pathlib.Path
        """

        return self.cache_dir / f"{cache_key}.npy"

    def _get_metadata_path(self, cache_key: str) -> pathlib.Path:
        """
        Get path to the metadata by cache key.

        :param cache_key: cache key
        :type cache_key: str

        :return: path to metadata file
        :rtype: pathlib.Path
        """
        return self.cache_dir / f"{cache_key}_meta.npy"

    def _is_cached(self, constraints: CatalogConstraints) -> bool:
        """
        Checks if catalog with these constraints is cached or not.

        :param constraints: catalog constraints
        :type constraints: CatalogConstraints

        :return: True if catalog with these constraints is cached else False
        :rtype: bool
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
        :type constraints: CatalogConstraints

        :return: loaded catalog
        :rtype: NDArray
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
        :type data: NDArray
        :param constraints: constraints
        :type constraints: CatalogConstraints
        """

        if not self.use_cache:
            return

        cache_key = self._generate_cache_key(constraints)
        cache_file = self._get_cache_path(cache_key)
        meta_file = self._get_metadata_path(cache_key)

        np.save(cache_file, data)
        metadata = {
            "constraints": constraints.to_dict(),
        }
        np.save(meta_file, metadata)

    def _load_raw_data(self) -> NDArray:
        """Loads raw data from file

        :return: cleaned raw data
        :rtype: NDArray

        :return: cleaned raw data
        :rtype: NDArray
        """

        raw_data = np.genfromtxt(
            fname=self.catalog_path,
            delimiter=";",
            dtype=None,
            names=True,
            encoding="utf-8",
            missing_values="",
            filling_values=None,
        )

        clean_data = self._clean_raw_data(raw_data)
        return clean_data

    @staticmethod
    def _apply_constraints(
        data: NDArray, constraints: CatalogConstraints
    ) -> NDArray:
        """Applies constraints to raw data

        :param data: data to constraint
        :type data: NDArray
        :param constraints: constraints
        :type constraints: CatalogConstraints

        :return: filtered data
        :rtype: NDArray
        """
        mask = data["v_mag"] <= constraints.max_magnitude
        if constraints.min_magnitude is not None:
            mask &= data["v_mag"] >= constraints.min_magnitude
        return data[mask]

    @staticmethod
    def _convert_to_structured_numpy(raw_data: NDArray) -> NDArray:
        """Converts raw genfromtxt data to structured numpy array

        :param raw_data: raw data
        :type raw_data: NDArray

        :return: structured numpy array
        :rtype: NDArray
        """
        number_of_stars = raw_data.shape[0]
        structured_data = np.zeros(number_of_stars, dtype=Catalog.STAR_DTYPE)

        structured_data["v_mag"] = raw_data["Vmag"].astype(np.float32)

        ra = np.deg2rad(raw_data["_RAJ2000"].astype(np.float32))
        dec = np.deg2rad(raw_data["_DEJ2000"].astype(np.float32))
        structured_data["ra"] = ra
        structured_data["dec"] = dec

        cos_ra = np.cos(ra)
        sin_ra = np.sin(ra)
        cos_dec = np.cos(dec)
        sin_dec = np.sin(dec)
        structured_data["x"] = (cos_ra * cos_dec).astype(np.float32)
        structured_data["y"] = (sin_ra * cos_dec).astype(np.float32)
        structured_data["z"] = sin_dec.astype(np.float32)

        structured_data["hip_id"] = raw_data["HIP"].astype(np.int32)

        return structured_data

    def get_stars(
        self, constraints: Optional[CatalogConstraints] = None
    ) -> NDArray:
        """Main catalog generation method

        :param constraints: constraints, optional, defaults to None
        :type constraints: CatalogConstraints | None

        :return: structured numpy array of stars
        :rtype: NDArray
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
        """ """
        if self._data is None:
            self.get_stars()
        return self._data

    @property
    def number_of_stars(self) -> int:
        """ """
        return self._data.shape[0]

    @property
    def constraints(self) -> Optional[CatalogConstraints]:
        """ """
        return self._constraints

    @staticmethod
    def _clean_raw_data(raw_data: NDArray) -> NDArray:
        """Removes units and rows with missing values
        in right ascension and declinations columns

        :param raw_data: source catalog data
        :type raw_data: NDArray
        :return: cleaned catalog data
        :rtype: NDArray
        """
        raw_data = raw_data[1:]
        mask = (raw_data["_RAJ2000"] != "") & (raw_data["_DEJ2000"] != "")
        clean_data = raw_data[mask]

        return clean_data


def main():
    # test catalog print
    catalog = Catalog(catalog_name="hip_data.tsv", use_cache=False)
    constraints = CatalogConstraints(
        max_magnitude=6.0,
    )
    data = catalog.get_stars(constraints=constraints)
    print(data[["x", "y", "z"]].view("f4"))
    print(data[["x", "y", "z"]])
    xyz = np.column_stack([data["x"], data["y"], data["z"]]).T
    print(xyz[0, :])


if __name__ == "__main__":
    main()
