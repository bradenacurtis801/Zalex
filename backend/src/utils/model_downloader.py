"""
Model downloader utility for production environments.
Downloads and extracts models from URLs at runtime.
"""

import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Handles downloading and extracting models from URLs."""

    def __init__(self, download_dir: str):
        """
        Initialize the model downloader.

        Args:
            download_dir: Directory to download models to
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_model(self, model_url: str, model_name: Optional[str] = None) -> str:
        """
        Download and extract a model from a URL.

        Args:
            model_url: URL to download the model from
            model_name: Optional name for the model directory

        Returns:
            str: Path to the extracted model directory

        Raises:
            Exception: If download or extraction fails
        """
        try:
            logger.info(f"Downloading model from: {model_url}")

            # Parse URL to get filename
            parsed_url = urlparse(model_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith((".zip", ".tar.gz", ".tar")):
                filename = "model.zip"

            # Create temporary file for download
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=filename
            ) as temp_file:
                temp_path = temp_file.name

            try:
                # Download the model
                logger.info(f"Downloading to temporary file: {temp_path}")
                response = requests.get(model_url, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"Download progress: {progress:.1f}%")

                logger.info(f"Download completed: {downloaded} bytes")

                # Determine model directory name
                if model_name:
                    model_dir_name = model_name
                else:
                    # Extract from filename or URL
                    model_dir_name = Path(filename).stem
                    if not model_dir_name:
                        model_dir_name = "downloaded_model"

                model_dir = self.download_dir / model_dir_name

                # Extract the model
                logger.info(f"Extracting model to: {model_dir}")
                self._extract_model(temp_path, model_dir)

                logger.info(
                    f"Model successfully downloaded and extracted to: {model_dir}"
                )
                return str(model_dir)

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Failed to download model from {model_url}: {e}")
            raise

    def _extract_model(self, archive_path: str, extract_dir: str) -> None:
        """
        Extract a model archive to the specified directory.

        Args:
            archive_path: Path to the archive file
            extract_dir: Directory to extract to
        """
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)

        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
        elif archive_path.endswith((".tar.gz", ".tgz")):
            import tarfile

            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_path)
        elif archive_path.endswith(".tar"):
            import tarfile

            with tarfile.open(archive_path, "r") as tar_ref:
                tar_ref.extractall(extract_path)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path}")

        # Check if we need to move files up one level (common with zip files)
        extracted_items = list(extract_path.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            # Move contents up one level
            inner_dir = extracted_items[0]
            for item in inner_dir.iterdir():
                shutil.move(str(item), str(extract_path))
            inner_dir.rmdir()

    def is_model_downloaded(self, model_name: str) -> bool:
        """
        Check if a model is already downloaded.

        Args:
            model_name: Name of the model to check

        Returns:
            bool: True if model exists and is valid
        """
        model_dir = self.download_dir / model_name
        if not model_dir.exists():
            return False

        # Check for required model files
        required_files = ["model_metadata.json", "category_embeddings.json"]
        for file_name in required_files:
            if not (model_dir / file_name).exists():
                logger.warning(
                    f"Model {model_name} is missing required file: {file_name}"
                )
                return False

        return True

    def get_model_path(self, model_name: str) -> Optional[str]:
        """
        Get the path to a downloaded model.

        Args:
            model_name: Name of the model

        Returns:
            str: Path to the model directory, or None if not found
        """
        model_dir = self.download_dir / model_name
        if model_dir.exists() and self.is_model_downloaded(model_name):
            return str(model_dir)
        return None
