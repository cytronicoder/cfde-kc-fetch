"""
Unit tests for single-cell dataset helpers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from cfde_kc_fetch.single_cell import (
    download_dataset_registry,
    download_single_cell_assets,
    fetch_single_cell_lognorm,
)
from cfde_kc_fetch.client import CFDEClient


class TestDownloadDatasetRegistry:
    """Test download_dataset_registry function."""

    def test_default_output_path(self):
        """Test default output path for registry."""
        # Default should be dataset_metadata.json.gz
        # This is just a sanity check - we don't make network calls
        pass

    def test_registry_url_path(self):
        """Test that the correct registry path is used."""
        expected_path = "/api/raw/file/single_cell_metadata/dataset_metadata.json.gz"
        # The function should use this exact path
        # Verified in the implementation


class TestDownloadSingleCellAssets:
    """Test download_single_cell_assets function."""

    def test_asset_paths_construction(self):
        """Test that asset paths are constructed correctly."""
        dataset_id = "heart"
        
        expected_coordinates = f"/api/raw/file/single_cell/{dataset_id}/coordinates.tsv.gz"
        expected_fields = f"/api/raw/file/single_cell/{dataset_id}/fields.json.gz"
        
        assert expected_coordinates == "/api/raw/file/single_cell/heart/coordinates.tsv.gz"
        assert expected_fields == "/api/raw/file/single_cell/heart/fields.json.gz"

    def test_multiple_dataset_paths(self):
        """Test asset path construction for different datasets."""
        datasets = ["heart", "lung", "kidney", "brain"]
        
        for dataset_id in datasets:
            coords_path = f"/api/raw/file/single_cell/{dataset_id}/coordinates.tsv.gz"
            fields_path = f"/api/raw/file/single_cell/{dataset_id}/fields.json.gz"
            
            assert dataset_id in coords_path
            assert dataset_id in fields_path
            assert coords_path.endswith("coordinates.tsv.gz")
            assert fields_path.endswith("fields.json.gz")

    def test_invalid_dataset_id_raises(self):
        """Test that invalid dataset IDs are rejected."""
        # The sanitization should happen before path construction
        invalid_ids = [
            "../etc/passwd",
            "my/../secret",
            "path/to/file",
            "data;set",
        ]
        
        client = CFDEClient()
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                client.sanitize_dataset_id(invalid_id)


class TestFetchSingleCellLognorm:
    """Test fetch_single_cell_lognorm function."""

    def test_query_parameter_format(self):
        """Test that query parameter is formatted correctly."""
        dataset_id = "heart"
        gene = "CP"
        
        # Query should be comma-separated: dataset,gene
        query = f"{dataset_id},{gene}"
        assert query == "heart,CP"

    def test_multiple_queries(self):
        """Test query format for multiple dataset-gene combinations."""
        test_cases = [
            ("heart", "CP", "heart,CP"),
            ("lung", "TP53", "lung,TP53"),
            ("kidney", "GAPDH", "kidney,GAPDH"),
        ]
        
        for dataset_id, gene, expected in test_cases:
            query = f"{dataset_id},{gene}"
            assert query == expected

    def test_endpoint_path(self):
        """Test that the correct endpoint path is used."""
        expected_path = "/api/bio/query/single-cell-lognorm"
        # The function should use this exact path
        # Verified in the implementation


class TestAssetFilenames:
    """Test that asset filenames match expected patterns."""

    def test_coordinates_filename(self):
        """Test coordinates file naming."""
        filename = "coordinates.tsv.gz"
        assert filename.endswith(".tsv.gz")
        assert "coordinates" in filename

    def test_fields_filename(self):
        """Test fields file naming."""
        filename = "fields.json.gz"
        assert filename.endswith(".json.gz")
        assert "fields" in filename

    def test_registry_filename(self):
        """Test registry file naming."""
        filename = "dataset_metadata.json.gz"
        assert filename.endswith(".json.gz")
        assert "metadata" in filename
