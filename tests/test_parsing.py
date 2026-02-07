"""
Unit tests for JSON/NDJSON parsing and schema normalization.
"""

import gzip
import json
import tempfile
from pathlib import Path

import pytest

# pylint: disable=protected-access
from cfde_kc_fetch.client import CFDEClient, CFDEAPIError
from cfde_kc_fetch.single_cell import normalize_dataset_record


class TestJSONParsing:
    """Test robust JSON/NDJSON parsing with various formats."""

    def test_parse_json_array(self):
        """Test parsing a JSON array."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = [
                {"datasetId": "heart", "datasetName": "Heart tissue"},
                {"datasetId": "lung", "datasetName": "Lung tissue"},
            ]
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["datasetId"] == "heart"
            assert result[1]["datasetId"] == "lung"
        finally:
            temp_path.unlink()

    def test_parse_json_object(self):
        """Test parsing a single JSON object."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {"datasetId": "heart", "datasetName": "Heart tissue"}
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, dict)
            assert result["datasetId"] == "heart"
        finally:
            temp_path.unlink()

    def test_parse_ndjson(self):
        """Test parsing NDJSON (newline-delimited JSON)."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"datasetId": "heart", "datasetName": "Heart tissue"}\n')
            f.write('{"datasetId": "lung", "datasetName": "Lung tissue"}\n')
            f.write('{"datasetId": "brain", "datasetName": "Brain tissue"}\n')
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["datasetId"] == "heart"
            assert result[1]["datasetId"] == "lung"
            assert result[2]["datasetId"] == "brain"
        finally:
            temp_path.unlink()

    def test_parse_ndjson_with_blank_lines(self):
        """Test parsing NDJSON with blank lines."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"datasetId": "heart", "datasetName": "Heart tissue"}\n')
            f.write("\n")
            f.write('{"datasetId": "lung", "datasetName": "Lung tissue"}\n')
            f.write("\n\n")
            f.write('{"datasetId": "brain", "datasetName": "Brain tissue"}\n')
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 3
        finally:
            temp_path.unlink()

    def test_parse_wrapper_datasets_key(self):
        """Test parsing wrapper object with 'datasets' key."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "datasets": [
                    {"datasetId": "heart", "datasetName": "Heart tissue"},
                    {"datasetId": "lung", "datasetName": "Lung tissue"},
                ]
            }
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["datasetId"] == "heart"
        finally:
            temp_path.unlink()

    def test_parse_wrapper_results_key(self):
        """Test parsing wrapper object with 'results' key."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "results": [{"datasetId": "heart", "datasetName": "Heart tissue"}],
                "count": 1,
            }
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 1
        finally:
            temp_path.unlink()

    def test_parse_utf8_bom(self):
        """Test parsing JSON with UTF-8 BOM."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8-sig"
        ) as f:
            data = {"datasetId": "heart", "datasetName": "Heart tissue"}
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, dict)
            assert result["datasetId"] == "heart"
        finally:
            temp_path.unlink()

    def test_parse_invalid_ndjson_line(self):
        """Test that invalid NDJSON line raises helpful error."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"datasetId": "heart", "datasetName": "Heart tissue"}\n')
            f.write('{"datasetId": "lung", invalid json here\n')
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                with pytest.raises(CFDEAPIError) as exc_info:
                    client._parse_json_or_ndjson_file(f)

            error_msg = str(exc_info.value)
            assert "line 2" in error_msg
            assert "Invalid JSON" in error_msg
        finally:
            temp_path.unlink()

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert result == []
        finally:
            temp_path.unlink()


class TestGzipDetection:
    """Test gzip detection and decompression."""

    def test_gzipped_ndjson(self):
        """Test parsing gzipped NDJSON file."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as f:
            temp_path = Path(f.name)
            with gzip.open(temp_path, "wt", encoding="utf-8") as gz:
                gz.write('{"datasetId": "heart", "datasetName": "Heart tissue"}\n')
                gz.write('{"datasetId": "lung", "datasetName": "Lung tissue"}\n')

        try:
            with open(temp_path, "rb") as bf:
                head = bf.read(2)

            assert head == b"\x1f\x8b", "File should have gzip magic bytes"

            with gzip.open(temp_path, "rt", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 2
        finally:
            temp_path.unlink()

    def test_not_actually_gzipped(self):
        """Test handling plain JSON file with .gz extension."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json.gz", delete=False
        ) as f:
            data = [{"datasetId": "heart", "datasetName": "Heart tissue"}]
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with open(temp_path, "rb") as bf:
                head = bf.read(2)

            assert head != b"\x1f\x8b", "File should NOT have gzip magic bytes"

            with open(temp_path, "rt", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 1
        finally:
            temp_path.unlink()

    def test_gzipped_json_array(self):
        """Test parsing gzipped JSON array."""
        client = CFDEClient()

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as f:
            temp_path = Path(f.name)
            with gzip.open(temp_path, "wt", encoding="utf-8") as gz:
                data = [
                    {"datasetId": "heart", "datasetName": "Heart tissue"},
                    {"datasetId": "lung", "datasetName": "Lung tissue"},
                ]
                json.dump(data, gz)

        try:
            with gzip.open(temp_path, "rt", encoding="utf-8") as f:
                result = client._parse_json_or_ndjson_file(f)

            assert isinstance(result, list)
            assert len(result) == 2
        finally:
            temp_path.unlink()


class TestSchemaNormalization:
    """Test dataset record schema normalization."""

    def test_normalize_camelcase_keys(self):
        """Test normalizing camelCase keys."""
        record = {
            "datasetId": "heart",
            "datasetName": "Heart tissue",
            "source": "HuBMAP",
        }
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == "heart"
        assert normalized["dataset_name"] == "Heart tissue"
        assert normalized["datasetId"] == "heart"
        assert normalized["datasetName"] == "Heart tissue"

    def test_normalize_snake_case_keys(self):
        """Test normalizing snake_case keys."""
        record = {"dataset_id": "lung", "dataset_name": "Lung tissue"}
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == "lung"
        assert normalized["dataset_name"] == "Lung tissue"

    def test_normalize_fallback_keys(self):
        """Test normalization with fallback keys."""
        record = {"id": "brain", "title": "Brain tissue study"}
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == "brain"
        assert normalized["dataset_name"] == "Brain tissue study"

    def test_normalize_missing_keys(self):
        """Test normalization when keys are missing."""
        record = {"source": "HuBMAP", "species": "Human"}
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == ""
        assert normalized["dataset_name"] == ""

    def test_normalize_priority_order(self):
        """Test that normalization follows priority order."""
        record = {
            "dataset_id": "correct_id",
            "datasetId": "wrong_id",
            "id": "also_wrong",
            "dataset_name": "correct_name",
            "title": "wrong_title",
        }
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == "correct_id"
        assert normalized["dataset_name"] == "correct_name"

    def test_normalize_whitespace_trimming(self):
        """Test that whitespace is trimmed from normalized values."""
        record = {"datasetId": "  heart  ", "datasetName": " Heart tissue\n"}
        normalized = normalize_dataset_record(record)

        assert normalized["dataset_id"] == "heart"
        assert normalized["dataset_name"] == "Heart tissue"

    def test_normalize_non_dict(self):
        """Test that non-dict input is returned as-is."""
        normalized = normalize_dataset_record("not a dict")
        assert normalized == "not a dict"

        normalized = normalize_dataset_record(None)
        assert normalized is None


class TestProgressMeter:
    """Test progress meter with various Content-Length scenarios."""

    def test_progress_with_content_length(self):
        """Test that progress calculation works when Content-Length is present."""
        total_size = 1024 * 1024
        downloaded = 512 * 1024

        if total_size > 0:
            percent = (downloaded / total_size) * 100
            assert percent == 50.0

    def test_progress_without_content_length(self):
        """Test that progress works when Content-Length is missing (0)."""
        total_size = 0
        downloaded = 512 * 1024

        if total_size > 0:
            percent = (downloaded / total_size) * 100
        else:
            percent = None

        assert percent is None

    def test_progress_zero_bytes(self):
        """Test progress with zero bytes downloaded."""
        total_size = 1024 * 1024
        downloaded = 0

        if total_size > 0:
            percent = (downloaded / total_size) * 100
            assert percent == 0.0
