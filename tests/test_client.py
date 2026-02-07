"""
Unit tests for the CFDE API client.
"""

import pytest


from cfde_kc_fetch.client import CFDEClient, CFDEAPIError


class TestCFDEClient:
    """Test the CFDEClient class."""

    def test_initialization(self):
        """Test client initialization with default parameters."""
        client = CFDEClient()
        assert client.base_url == "https://cfde.hugeampkpnbi.org"
        assert client.timeout == 60
        assert client.session is not None

    def test_initialization_custom(self):
        """Test client initialization with custom parameters."""
        client = CFDEClient(
            base_url="https://example.com",
            timeout=120,
            retries=5,
            user_agent="test-agent/1.0",
        )
        assert client.base_url == "https://example.com"
        assert client.timeout == 120
        assert "User-Agent" in client.session.headers
        assert client.session.headers["User-Agent"] == "test-agent/1.0"


class TestURLBuilding:
    """Test URL construction for various endpoints."""

    def test_dataset_registry_url(self):
        """Test dataset registry URL construction."""
        client = CFDEClient()
        path = "/api/raw/file/single_cell_metadata/dataset_metadata.json.gz"
        expected = (
            "https://cfde.hugeampkpnbi.org"
            "/api/raw/file/single_cell_metadata/dataset_metadata.json.gz"
        )

        from urllib.parse import urljoin

        url = urljoin(client.base_url, path)
        assert url == expected

    def test_single_cell_coordinates_url(self):
        """Test single-cell coordinates URL construction."""
        client = CFDEClient()
        dataset_id = "heart"
        path = f"/api/raw/file/single_cell/{dataset_id}/coordinates.tsv.gz"
        expected = (
            "https://cfde.hugeampkpnbi.org"
            "/api/raw/file/single_cell/heart/coordinates.tsv.gz"
        )

        from urllib.parse import urljoin

        url = urljoin(client.base_url, path)
        assert url == expected

    def test_single_cell_fields_url(self):
        """Test single-cell fields URL construction."""
        client = CFDEClient()
        dataset_id = "lung"
        path = f"/api/raw/file/single_cell/{dataset_id}/fields.json.gz"
        expected = (
            "https://cfde.hugeampkpnbi.org"
            "/api/raw/file/single_cell/lung/fields.json.gz"
        )

        from urllib.parse import urljoin

        url = urljoin(client.base_url, path)
        assert url == expected

    def test_gene_expression_query_url(self):
        """Test gene expression query URL construction."""
        client = CFDEClient()
        path = "/api/bio/query/single-cell-lognorm"
        dataset_id = "heart"
        gene = "CP"
        params = {"q": f"{dataset_id},{gene}"}

        from urllib.parse import urljoin, urlencode

        base_url = urljoin(client.base_url, path)
        expected = f"{base_url}?q=heart%2CCP"

        url = f"{base_url}?{urlencode(params)}"
        assert url == expected

    def test_url_sanitization(self):
        """Test that sanitized IDs produce valid URLs."""
        client = CFDEClient()

        valid_ids = ["heart", "lung-v1", "kidney_2.0", "brain.alpha-1"]
        for dataset_id in valid_ids:
            sanitized = client.sanitize_dataset_id(dataset_id)
            path = f"/api/raw/file/single_cell/{sanitized}/coordinates.tsv.gz"

            from urllib.parse import urljoin

            url = urljoin(client.base_url, path)
            assert "single_cell" in url
            assert sanitized in url

    def test_url_no_double_slashes(self):
        """Test that URL construction doesn't create double slashes."""
        client = CFDEClient()

        path1 = "/api/raw/file/single_cell/heart/coordinates.tsv.gz"
        path2 = "api/raw/file/single_cell/heart/coordinates.tsv.gz"

        from urllib.parse import urljoin

        url1 = urljoin(client.base_url, path1)
        url2 = urljoin(client.base_url, path2)

        assert "//api" not in url1
        assert "//api" not in url2


class TestErrorHandling:
    """Test error handling in the client."""

    def test_cfde_api_error_creation(self):
        """Test CFDEAPIError exception creation."""
        error = CFDEAPIError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_invalid_dataset_id_raises(self):
        """Test that invalid dataset IDs raise ValueError."""
        client = CFDEClient()

        with pytest.raises(ValueError):
            client.sanitize_dataset_id("../etc/passwd")

    def test_invalid_gene_raises(self):
        """Test that invalid gene symbols raise ValueError."""
        client = CFDEClient()

        with pytest.raises(ValueError):
            client.sanitize_gene("gene; DROP TABLE")


class TestSessionConfiguration:
    """Test HTTP session configuration."""

    def test_session_has_user_agent(self):
        """Test that session includes User-Agent header."""
        client = CFDEClient()
        assert "User-Agent" in client.session.headers
        assert "cfde-kc-fetch" in client.session.headers["User-Agent"]

    def test_custom_user_agent(self):
        """Test custom User-Agent configuration."""
        custom_ua = "my-app/2.0"
        client = CFDEClient(user_agent=custom_ua)
        assert client.session.headers["User-Agent"] == custom_ua

    def test_session_has_retry_adapter(self):
        """Test that session includes retry adapter."""
        client = CFDEClient(retries=5)

        assert "http://" in client.session.adapters
        assert "https://" in client.session.adapters


class TestChunkSize:
    """Test chunk size configuration."""

    def test_chunk_size_constant(self):
        """Test that chunk size is set to 8MB."""
        client = CFDEClient()
        assert client.CHUNK_SIZE == 8 * 1024 * 1024

    def test_chunk_size_is_reasonable(self):
        """Test that chunk size is in reasonable range."""
        client = CFDEClient()
        assert 1024 * 1024 <= client.CHUNK_SIZE <= 100 * 1024 * 1024


def test_download_gzipped_json_parses_ndjson_plain(tmp_path):
    """NDJSON (plain text) should be parsed as a list of objects."""
    content = '{"a": 1}\n{"b": 2}\n'
    p = tmp_path / "registry.json.gz"
    p.write_text(content, encoding="utf-8")

    client = CFDEClient()
    client.download_file = lambda path, output_path, overwrite=False: p

    data = client.download_gzipped_json("/fake", p, overwrite=True)
    assert isinstance(data, list)
    assert data[0]["a"] == 1
    assert data[1]["b"] == 2


def test_download_gzipped_json_parses_ndjson_gz(tmp_path):
    """NDJSON gzipped should be parsed as a list of objects."""
    content = '{"x": 10}\n{"y": 20}\n'
    p = tmp_path / "registry.json.gz"
    import gzip

    with gzip.open(p, "wb") as f:
        f.write(content.encode("utf-8"))

    client = CFDEClient()
    client.download_file = lambda path, output_path, overwrite=False: p

    data = client.download_gzipped_json("/fake", p, overwrite=True)
    assert isinstance(data, list)
    assert data[0]["x"] == 10
    assert data[1]["y"] == 20


def test_download_gzipped_json_parses_json_array(tmp_path):
    """A JSON array should be parsed as a list."""
    content = '[{"a":1},{"b":2}]'
    p = tmp_path / "registry.json.gz"
    p.write_text(content, encoding="utf-8")

    client = CFDEClient()
    client.download_file = lambda path, output_path, overwrite=False: p

    data = client.download_gzipped_json("/fake", p, overwrite=True)
    assert isinstance(data, list)
    assert data[0]["a"] == 1
    assert data[1]["b"] == 2
