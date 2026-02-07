"""
HTTP client for CFDE Knowledge Center API with retry logic and streaming downloads.
"""

import gzip
import json
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CFDEAPIError(Exception):
    """Exception raised when the CFDE API returns an error."""


class CFDEClient:
    """
    A client for interacting with the CFDE Knowledge Center API.

    Handles HTTP requests with automatic retries, timeouts, and streaming downloads.
    """

    BASE_URL = "https://cfde.hugeampkpnbi.org"
    DEFAULT_TIMEOUT = 60
    DEFAULT_RETRIES = 3
    CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB chunks for streaming

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        user_agent: str = "cfde-kc-fetch/0.1.0",
    ):
        """
        Initialize the CFDE API client.

        Args:
            base_url: Base URL for the CFDE API
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
            user_agent: User agent string for requests
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._create_session(retries, user_agent)

    def _create_session(self, retries: int, user_agent: str) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

        # Configure retry strategy
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @staticmethod
    def sanitize_dataset_id(dataset_id: str) -> str:
        """
        Sanitize dataset ID to prevent path traversal attacks.

        Args:
            dataset_id: The dataset identifier to sanitize

        Returns:
            Sanitized dataset ID

        Raises:
            ValueError: If dataset_id contains invalid characters
        """
        if not re.match(r"^[A-Za-z0-9._-]+$", dataset_id):
            raise ValueError(
                f"Invalid dataset_id '{dataset_id}'. "
                "Must contain only alphanumeric characters, dots, underscores, and hyphens."
            )
        return dataset_id

    @staticmethod
    def sanitize_gene(gene: str) -> str:
        """
        Sanitize gene symbol to prevent injection attacks.

        Args:
            gene: The gene symbol to sanitize

        Returns:
            Sanitized gene symbol

        Raises:
            ValueError: If gene contains invalid characters
        """
        if not re.match(r"^[A-Za-z0-9._-]+$", gene):
            raise ValueError(
                f"Invalid gene '{gene}'. "
                "Must contain only alphanumeric characters, dots, underscores, and hyphens."
            )
        return gene

    def get_json(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform a GET request and return JSON response.

        Args:
            path: API endpoint path (relative to base_url)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            CFDEAPIError: If the request fails or returns an error
        """
        url = urljoin(self.base_url, path)
        print(f"[GET] {url}")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Try to extract error details from JSON response
            error_msg = f"HTTP {e.response.status_code} for {url}"
            try:
                error_data = e.response.json()
                error_msg += f"\nDetails: {json.dumps(error_data, indent=2)[:500]}"
            except (ValueError, KeyError, AttributeError):
                error_msg += f"\nResponse: {e.response.text[:500]}"
            raise CFDEAPIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise CFDEAPIError(f"Request failed for {url}: {str(e)}") from e

    def download_file(  # noqa: C901
        self,
        path: str,
        output_path: Path,
        overwrite: bool = False,
        decompress: bool = False,
        keep_gz: bool = True,
    ) -> Path:
        """
        Download a file from the API with streaming and optional decompression.

        Args:
            path: API endpoint path (relative to base_url)
            output_path: Local path to save the file
            overwrite: Whether to overwrite existing files
            decompress: Whether to decompress .gz files
            keep_gz: Whether to keep the .gz file after decompression

        Returns:
            Path to the downloaded (or decompressed) file

        Raises:
            CFDEAPIError: If the download fails
            FileExistsError: If file exists and overwrite is False
        """
        output_path = Path(output_path)

        # Check if file exists
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {output_path}. Use overwrite=True to replace."
            )

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        url = urljoin(self.base_url, path)
        print(f"[DOWNLOAD] {url} -> {output_path}")

        try:
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get("content-length", 0))

            # Stream to file and show progress
            downloaded = self._stream_response_to_file(response, output_path, total_size)

            print(f"[SAVED] {output_path} ({downloaded / 1024 / 1024:.2f} MB)")

            # Decompress if requested
            if decompress and output_path.suffix == ".gz":
                return self._decompress_gz(output_path, keep_gz)

            return output_path

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code} for {url}"
            try:
                error_data = e.response.json()
                error_msg += f"\nDetails: {json.dumps(error_data, indent=2)[:500]}"
            except (ValueError, KeyError, AttributeError):
                error_msg += f"\nResponse: {e.response.text[:500]}"
            raise CFDEAPIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise CFDEAPIError(f"Download failed for {url}: {str(e)}") from e

    def _stream_response_to_file(self, response, output_path: Path, total_size: int) -> int:
        """Stream response content to file and display progress. Returns bytes downloaded."""
        downloaded = 0
        start_time = time.time()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if not chunk:
                    continue

                f.write(chunk)
                downloaded += len(chunk)

                # Progress indicator
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0
                    print(
                        f"\r  Progress: {percent:.1f}% "
                        f"({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB) "
                        f"@ {speed:.1f} MB/s",
                        end="",
                    )
                else:
                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0
                    print(
                        f"\r  Downloaded: {downloaded/1024/1024:.1f} MB "
                        f"@ {speed:.1f} MB/s",
                        end="",
                    )

        # Print newline after streaming
        print()
        return downloaded

    def _decompress_gz(self, gz_path: Path, keep_gz: bool = True) -> Path:
        """Decompress a .gz file and optionally remove the original gz file."""
        decompressed_path = gz_path.with_suffix("")
        print(f"[DECOMPRESS] {gz_path} -> {decompressed_path}")

        with gzip.open(gz_path, "rb") as f_in:
            with open(decompressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"[SAVED] {decompressed_path}")

        if not keep_gz:
            gz_path.unlink()
            print(f"[REMOVED] {gz_path}")

        return decompressed_path

    def download_gzipped_json(
        self, path: str, output_path: Path, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Download a .json.gz file and return parsed JSON.

        Auto-detects whether the file is actually gzipped by checking magic bytes,
        so it works regardless of server compression behavior.

        Args:
            path: API endpoint path (relative to base_url)
            output_path: Local path to save the .json.gz file
            overwrite: Whether to overwrite existing files

        Returns:
            Parsed JSON content

        Raises:
            CFDEAPIError: If the download or parsing fails
        """
        gzip_magic = b"\x1f\x8b"

        # Download the file
        downloaded_path = self.download_file(path, output_path, overwrite=overwrite)

        # Parse JSON, auto-detecting gzip by magic bytes
        print(f"[PARSE] {downloaded_path}")
        try:
            # Read first 2 bytes to check for gzip magic
            with open(downloaded_path, "rb") as f:
                head = f.read(2)

            if head == gzip_magic:
                # File is gzipped
                with gzip.open(downloaded_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                # File is plain JSON (requests auto-decompressed)
                with open(downloaded_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)

            return data
        except Exception as e:
            raise CFDEAPIError(
                f"Failed to parse JSON from {downloaded_path}: {str(e)}"
            ) from e
