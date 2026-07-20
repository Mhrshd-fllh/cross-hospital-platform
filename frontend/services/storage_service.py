"""
Mock implementation of the StorageService for development and testing.
Returns simulated data for frontend development.
"""

import hashlib
import uuid
from typing import Optional, Dict, Any
from . import StorageService

class MockStorageService(StorageService):
    """Mock implementation of StorageService."""

    def __init__(self):
        # In-memory storage for mock files
        self._stored_files: Dict[str, bytes] = {}
        self._file_metadata: Dict[str, Dict[str, Any]] = {}

    def upload_file(self, file_data: bytes, path: str) -> str:
        """
        Simulate uploading a file to storage.

        Args:
            file_data: The file data to upload
            path: The storage path (e.g., "bucket/file.dcm")

        Returns:
            str: The storage path where the file was stored
        """
        # Store the file data
        self._stored_files[path] = file_data

        # Store metadata
        self._file_metadata[path] = {
            "size": len(file_data),
            "uploaded_at": datetime.now().isoformat(),
            "content_type": self._guess_content_type(path),
            "md5": hashlib.md5(file_data).hexdigest() if file_data else None
        }

        return path

    def download_file(self, path: str) -> bytes:
        """
        Simulate downloading a file from storage.

        Args:
            path: The storage path of the file to download

        Returns:
            bytes: The file data

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if path not in self._stored_files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._stored_files[path]

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            path: The storage path to check

        Returns:
            bool: True if the file exists, False otherwise
        """
        return path in self._stored_files

    def delete_file(self, path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            path: The storage path of the file to delete

        Returns:
            bool: True if the file was deleted, False if it didn't exist
        """
        if path in self._stored_files:
            del self._stored_files[path]
            del self._file_metadata[path]
            return True
        return False

    def get_file_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a stored file.

        Args:
            path: The storage path

        Returns:
            Dict containing file metadata, or None if file not found
        """
        return self._file_metadata.get(path)

    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files by

        Returns:
            List of file paths matching the prefix
        """
        if prefix:
            return [path for path in self._stored_files.keys() if path.startswith(prefix)]
        return list(self._stored_files.keys())

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary containing storage stats
        """
        total_size = sum(len(data) for data in self._stored_files.values())
        file_count = len(self._stored_files)

        return {
            "total_files": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_file_size": round(total_size / file_count, 2) if file_count > 0 else 0
        }

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type based on file extension."""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'dcm': 'application/dicom',
            'dicom': 'application/dicom',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tif': 'image/tiff',
            'tiff': 'image/tiff',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'json': 'application/json'
        }
        return content_types.get(extension, 'application/octet-stream')

# Factory function
def create_storage_service() -> StorageService:
    """Create an instance of the mock StorageService."""
    return MockStorageService()

# For backward compatibility, also export the classes
__all__ = [
    'StorageService',
    'MockStorageService',
    'create_storage_service'
]