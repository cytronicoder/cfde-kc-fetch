"""
Unit tests for input sanitization and validation.
"""

import pytest

from cfde_kc_fetch.client import CFDEClient


class TestDatasetIDSanitization:
    """Test dataset ID sanitization to prevent path traversal attacks."""

    def test_valid_alphanumeric(self):
        """Valid alphanumeric dataset IDs should pass."""
        assert CFDEClient.sanitize_dataset_id("heart") == "heart"
        assert CFDEClient.sanitize_dataset_id("lung123") == "lung123"
        assert CFDEClient.sanitize_dataset_id("KIDNEY") == "KIDNEY"

    def test_valid_with_dots(self):
        """Valid dataset IDs with dots should pass."""
        assert CFDEClient.sanitize_dataset_id("dataset.v1") == "dataset.v1"
        assert CFDEClient.sanitize_dataset_id("sample.1.0") == "sample.1.0"

    def test_valid_with_underscores(self):
        """Valid dataset IDs with underscores should pass."""
        assert CFDEClient.sanitize_dataset_id("my_dataset") == "my_dataset"
        assert CFDEClient.sanitize_dataset_id("heart_v2") == "heart_v2"

    def test_valid_with_hyphens(self):
        """Valid dataset IDs with hyphens should pass."""
        assert CFDEClient.sanitize_dataset_id("my-dataset") == "my-dataset"
        assert CFDEClient.sanitize_dataset_id("heart-lung-v1") == "heart-lung-v1"

    def test_valid_mixed(self):
        """Valid dataset IDs with mixed allowed characters should pass."""
        assert CFDEClient.sanitize_dataset_id("My_Dataset-v1.0") == "My_Dataset-v1.0"

    def test_invalid_path_traversal(self):
        """Dataset IDs with path traversal attempts should fail."""
        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("../etc/passwd")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("../../secret")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("my/../data")

    def test_invalid_slashes(self):
        """Dataset IDs with slashes should fail."""
        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("path/to/file")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("my\\windows\\path")

    def test_invalid_special_chars(self):
        """Dataset IDs with special characters should fail."""
        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("dataset@v1")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("data$set")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("my dataset")

        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("data;set")

    def test_invalid_null_bytes(self):
        """Dataset IDs with null bytes should fail."""
        with pytest.raises(ValueError, match="Invalid dataset_id"):
            CFDEClient.sanitize_dataset_id("data\x00set")


class TestGeneSanitization:
    """Test gene symbol sanitization to prevent injection attacks."""

    def test_valid_simple_genes(self):
        """Valid simple gene symbols should pass."""
        assert CFDEClient.sanitize_gene("CP") == "CP"
        assert CFDEClient.sanitize_gene("TP53") == "TP53"
        assert CFDEClient.sanitize_gene("GAPDH") == "GAPDH"

    def test_valid_with_numbers(self):
        """Valid gene symbols with numbers should pass."""
        assert CFDEClient.sanitize_gene("CD8A") == "CD8A"
        assert CFDEClient.sanitize_gene("HLA-DRB1") == "HLA-DRB1"

    def test_valid_with_hyphens(self):
        """Valid gene symbols with hyphens should pass."""
        assert CFDEClient.sanitize_gene("HLA-A") == "HLA-A"
        assert CFDEClient.sanitize_gene("BRCA1-NBR2") == "BRCA1-NBR2"

    def test_valid_with_dots(self):
        """Valid gene symbols with dots should pass."""
        assert CFDEClient.sanitize_gene("LOC100.1") == "LOC100.1"

    def test_valid_with_underscores(self):
        """Valid gene symbols with underscores should pass."""
        assert CFDEClient.sanitize_gene("GENE_1") == "GENE_1"

    def test_invalid_special_chars(self):
        """Gene symbols with special characters should fail."""
        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("TP53;DROP TABLE")

        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("GENE@123")

        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("MY GENE")

    def test_invalid_sql_injection(self):
        """Gene symbols with SQL injection attempts should fail."""
        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("' OR '1'='1")

        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("gene'; DROP TABLE--")

    def test_invalid_path_traversal(self):
        """Gene symbols with path traversal attempts should fail."""
        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("../etc/passwd")

        with pytest.raises(ValueError, match="Invalid gene"):
            CFDEClient.sanitize_gene("gene/../../file")
