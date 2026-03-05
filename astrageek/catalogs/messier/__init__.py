"""Package with astronomical catalogs, besides stars and planets."""

from astrageek.catalogs.messier.messier_catalog import (
    MessierCatalog,
    MessierType,
    print_catalog_info,
)

__all__ = [
    "MessierCatalog",
    "MessierType",
    "print_catalog_info",
]
