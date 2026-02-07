"""
CFDE Knowledge Center Dataset Fetcher

A Python package for downloading single-cell datasets and querying gene expression
from the CFDE (Common Fund Data Ecosystem) Knowledge Center API.

For documentation, see: https://cfde.hugeampkpnbi.org/docs
"""

__version__ = "0.2.0"
__author__ = "Zeyu Yao"

from .client import CFDEClient
from .single_cell import (
    download_dataset_registry,
    download_single_cell_assets,
    fetch_single_cell_lognorm,
    normalize_dataset_record,
)

__all__ = [
    "CFDEClient",
    "download_dataset_registry",
    "download_single_cell_assets",
    "fetch_single_cell_lognorm",
    "normalize_dataset_record",
]
