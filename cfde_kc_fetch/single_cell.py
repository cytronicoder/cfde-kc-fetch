"""
Dataset helpers for CFDE Knowledge Center single-cell data.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .client import CFDEClient, CFDEAPIError


def download_dataset_registry(
    output_path: str = "dataset_metadata.json.gz",
    overwrite: bool = False,
    client: Optional[CFDEClient] = None,
) -> Dict[str, Any]:
    """
    Download the single-cell dataset registry and return parsed JSON.

    The registry contains metadata for all available single-cell datasets,
    including dataset IDs, names, descriptions, and other attributes.

    Args:
        output_path: Path to save the downloaded registry file
        overwrite: Whether to overwrite existing files
        client: Optional CFDEClient instance (creates default if not provided)

    Returns:
        Parsed JSON content of the dataset registry

    Raises:
        CFDEAPIError: If the download or parsing fails

    Example:
        >>> registry = download_dataset_registry("data/registry.json.gz")
        >>> print(f"Found {len(registry)} datasets")
    """
    if client is None:
        client = CFDEClient()

    path = "/api/raw/file/single_cell_metadata/dataset_metadata.json.gz"
    output_path = Path(output_path)

    return client.download_gzipped_json(path, output_path, overwrite=overwrite)


def download_single_cell_assets(
    dataset_id: str,
    output_dir: str = ".",
    overwrite: bool = False,
    decompress: bool = False,
    client: Optional[CFDEClient] = None,
) -> Dict[str, Path]:
    """
    Download single-cell dataset assets for a given dataset ID.

    Downloads the following files:
    - coordinates.tsv.gz: Cell coordinate data for visualization
    - fields.json.gz: Field definitions and metadata

    Args:
        dataset_id: The dataset identifier (e.g., "heart", "lung")
        output_dir: Directory to save downloaded files
        overwrite: Whether to overwrite existing files
        decompress: Whether to decompress .gz files (keeps .gz by default)
        client: Optional CFDEClient instance (creates default if not provided)

    Returns:
        Dictionary mapping asset names to downloaded file paths

    Raises:
        CFDEAPIError: If any download fails
        ValueError: If dataset_id is invalid

    Example:
        >>> assets = download_single_cell_assets("heart", "data/heart")
        >>> print(f"Downloaded: {list(assets.keys())}")
    """
    if client is None:
        client = CFDEClient()

    dataset_id = client.sanitize_dataset_id(dataset_id)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets = {
        "coordinates": f"/api/raw/file/single_cell/{dataset_id}/coordinates.tsv.gz",
        "fields": f"/api/raw/file/single_cell/{dataset_id}/fields.json.gz",
    }

    downloaded = {}

    for asset_name, path in assets.items():
        filename = path.rsplit("/", maxsplit=1)[-1]
        output_path = output_dir / filename

        try:
            downloaded_path = client.download_file(
                path=path,
                output_path=output_path,
                overwrite=overwrite,
                decompress=decompress,
                keep_gz=True,
            )
            downloaded[asset_name] = downloaded_path
        except (OSError, CFDEAPIError) as e:
            print(f"[WARNING] Failed to download {asset_name}: {e}")

    if not downloaded:
        raise ValueError(f"Failed to download any assets for dataset '{dataset_id}'")

    return downloaded


def fetch_single_cell_lognorm(
    dataset_id: str,
    gene: str,
    output_path: Optional[str] = None,
    client: Optional[CFDEClient] = None,
) -> Dict[str, Any]:
    """
    Query log-normalized single-cell gene expression data.

    Queries the single-cell-lognorm endpoint for gene expression values
    across cells in the specified dataset.

    Args:
        dataset_id: The dataset identifier (e.g., "heart", "lung")
        gene: Gene symbol (e.g., "CP", "TP53")
        output_path: Optional path to save the JSON response
        client: Optional CFDEClient instance (creates default if not provided)

    Returns:
        Parsed JSON response containing gene expression data

    Raises:
        CFDEAPIError: If the query fails
        ValueError: If dataset_id or gene is invalid

    Example:
        >>> data = fetch_single_cell_lognorm("heart", "CP", "data/heart/genes/CP.json")
        >>> print(f"Expression data for {data.get('gene', gene)}")
    """
    if client is None:
        client = CFDEClient()

    dataset_id = client.sanitize_dataset_id(dataset_id)
    gene = client.sanitize_gene(gene)

    query = f"{dataset_id},{gene}"
    path = "/api/bio/query/single-cell-lognorm"
    params = {"q": query}

    data = client.get_json(path, params=params)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"[SAVED] {output_path}")

    return data
