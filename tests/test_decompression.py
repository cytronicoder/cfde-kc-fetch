"""
Unit tests for gzip decompression functionality.

Tests cover both real gzipped files and "fake gz" files (plain content with .gz extension).
"""

import gzip
import pytest

from cfde_kc_fetch.client import CFDEClient, CFDEAPIError


class TestDecompression:
    """Test decompress_gz method with various file types."""

    def test_decompress_real_gzip(self, tmp_path):
        """Test decompression of a real gzipped file."""
        client = CFDEClient()
        gz_file = tmp_path / "test.txt.gz"
        original_content = b"hello\nworld\n"

        with gzip.open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file, keep_gz=True)

        assert decompressed == tmp_path / "test.txt"
        assert decompressed.exists()

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content
        assert gz_file.exists()

    def test_decompress_fake_gz_tsv(self, tmp_path):
        """Test handling of 'fake gz' file - plain TSV with .gz extension."""
        client = CFDEClient()
        gz_file = tmp_path / "coordinates.tsv.gz"
        original_content = b"X\tY\tZ\n1\t2\t3\n4\t5\t6\n"

        with open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file, keep_gz=True)

        assert decompressed == tmp_path / "coordinates.tsv"
        assert decompressed.exists()

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content

    def test_decompress_fake_gz_json(self, tmp_path):
        """Test handling of 'fake gz' file - plain JSON with .gz extension."""
        client = CFDEClient()
        gz_file = tmp_path / "fields.json.gz"
        original_content = b'{"field1": "value1", "field2": 123}\n'

        with open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file, keep_gz=True)
        assert decompressed == tmp_path / "fields.json"
        assert decompressed.exists()

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content

    def test_decompress_empty_file(self, tmp_path):
        """Test that empty files raise ValueError."""
        client = CFDEClient()
        gz_file = tmp_path / "empty.txt.gz"
        gz_file.touch()

        with pytest.raises(ValueError, match="File is empty"):
            client.decompress_gz(gz_file)

    def test_decompress_remove_original(self, tmp_path):
        """Test that keep_gz=False removes the original file."""
        client = CFDEClient()
        gz_file = tmp_path / "test.txt.gz"
        original_content = b"test content\n"

        with gzip.open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file, keep_gz=False)

        assert decompressed.exists()
        assert not gz_file.exists()

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content

    def test_decompress_corrupted_gzip(self, tmp_path):
        """Test that corrupted gzip files raise appropriate errors."""
        client = CFDEClient()

        gz_file = tmp_path / "corrupted.txt.gz"

        with open(gz_file, "wb") as f:
            f.write(b"\x1f\x8b\x08\x00\x00\x00\x00\x00")
            f.write(b"not valid gzip data")

        with pytest.raises(CFDEAPIError, match="Gzip decompression failed"):
            client.decompress_gz(gz_file)

    def test_decompress_preserves_directory_structure(self, tmp_path):
        """Test that decompression works with nested directories."""
        client = CFDEClient()
        subdir = tmp_path / "data" / "raw"
        subdir.mkdir(parents=True, exist_ok=True)

        gz_file = subdir / "test.json.gz"
        original_content = b'{"key": "value"}\n'

        with gzip.open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file)

        assert decompressed == subdir / "test.json"
        assert decompressed.exists()

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content

    def test_decompress_binary_content(self, tmp_path):
        """Test decompression with binary content (not just text)."""
        client = CFDEClient()
        gz_file = tmp_path / "binary.dat.gz"
        original_content = bytes(range(256))

        with gzip.open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file)

        with open(decompressed, "rb") as f:
            content = f.read()

        assert content == original_content

    def test_decompress_large_content(self, tmp_path):
        """Test decompression with larger files to ensure streaming works."""
        client = CFDEClient()
        gz_file = tmp_path / "large.txt.gz"
        original_content = b"A" * (1024 * 1024)

        with gzip.open(gz_file, "wb") as f:
            f.write(original_content)

        decompressed = client.decompress_gz(gz_file)

        with open(decompressed, "rb") as f:
            content = f.read()

        assert len(content) == len(original_content)
        assert content == original_content


class TestDownloadFileWithDecompression:
    """Test the download_file method with decompress option."""

    def test_download_calls_decompress_for_gz_files(self, tmp_path, monkeypatch):
        """Test that download_file calls decompress_gz when decompress=True."""
        client = CFDEClient()
        decompress_called = []
        original_decompress = client.decompress_gz

        def mock_decompress(gz_path, keep_gz=True):
            """Mock decompress that records calls and delegates to original."""
            decompress_called.append((gz_path, keep_gz))
            return original_decompress(gz_path, keep_gz)

        monkeypatch.setattr(client, "decompress_gz", mock_decompress)

        class MockResponse:
            """Simple mock for requests response providing byte chunks."""

            status_code = 200
            headers = {"content-length": "100"}

            def raise_for_status(self):
                """No-op status check."""

            def iter_content(self, chunk_size=None):
                """Yield a single byte chunk for testing streaming."""
                del chunk_size
                yield b"test content"

        def mock_get(*_args, **_kwargs):
            """Return a MockResponse instance for requests.get replacement."""
            return MockResponse()

        monkeypatch.setattr(client.session, "get", mock_get)
        output_path = tmp_path / "test.txt.gz"
        result = client.download_file(
            "/test/file.gz", output_path, overwrite=True, decompress=True, keep_gz=True
        )

        assert len(decompress_called) == 1
        assert decompress_called[0][0] == output_path
        assert decompress_called[0][1]
        assert result == tmp_path / "test.txt"

    def test_download_skips_decompress_for_non_gz(self, tmp_path, monkeypatch):
        """Test that download_file skips decompression for non-.gz files."""
        client = CFDEClient()
        decompress_called = []

        def mock_decompress(gz_path, _keep_gz=True):
            """Mock decompress for non-.gz path that records calls."""
            decompress_called.append(True)
            return gz_path.with_suffix("")

        monkeypatch.setattr(client, "decompress_gz", mock_decompress)

        class MockResponse:
            """Simple mock for requests response providing byte chunks."""

            status_code = 200
            headers = {"content-length": "100"}

            def raise_for_status(self):
                """No-op status check."""

            def iter_content(self, chunk_size=None):
                """Yield a single byte chunk for testing streaming."""
                # Accept chunk_size for compatibility with requests and mark it used
                del chunk_size
                yield b"test content"

        def mock_get(*_args, **_kwargs):
            """Return a MockResponse instance for requests.get replacement."""
            return MockResponse()

        monkeypatch.setattr(client.session, "get", mock_get)
        output_path = tmp_path / "test.txt"
        result = client.download_file(
            "/test/file.txt", output_path, overwrite=True, decompress=True
        )

        assert len(decompress_called) == 0
        assert result == output_path
