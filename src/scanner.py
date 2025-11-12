"""
VMU File Scanner
Recursively scans directories for VMU save files
"""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class VMUScanner:
    """Scans directories for VMU save files"""

    # Supported file extensions
    EXTENSIONS = {'.vmu', '.vms', '.dci', '.bin'}

    def __init__(self):
        self.files_found = []

    def scan(self, path: Path) -> List[Path]:
        """
        Recursively scan directory for VMU files

        Args:
            path: Directory to scan

        Returns:
            List of Path objects for found VMU files
        """
        logger.info(f"Scanning directory: {path}")
        self.files_found = []

        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if path.is_file():
            # Single file provided
            if self._is_vmu_file(path):
                self.files_found.append(path)
        else:
            # Recursively scan directory
            self._scan_directory(path)

        logger.info(f"Found {len(self.files_found)} VMU files")
        return sorted(self.files_found)

    def _scan_directory(self, directory: Path):
        """Recursively scan directory"""
        try:
            for item in directory.iterdir():
                if item.is_file() and self._is_vmu_file(item):
                    self.files_found.append(item)
                    logger.debug(f"Found VMU file: {item}")
                elif item.is_dir():
                    # Recursively scan subdirectories
                    self._scan_directory(item)
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")

    def _is_vmu_file(self, file_path: Path) -> bool:
        """
        Check if file is a VMU save file

        Args:
            file_path: Path to check

        Returns:
            True if file has VMU extension and reasonable size
        """
        # Check extension
        if file_path.suffix.lower() not in self.EXTENSIONS:
            return False

        # Check file size (VMU files are typically between 512 bytes and 128KB)
        try:
            size = file_path.stat().st_size
            if size < 512 or size > 131072:  # 128KB
                logger.debug(f"Skipping {file_path}: size {size} out of range")
                return False
        except OSError:
            return False

        return True

    def get_statistics(self) -> dict:
        """Get scanning statistics"""
        return {
            'total_files': len(self.files_found),
            'by_extension': self._count_by_extension()
        }

    def _count_by_extension(self) -> dict:
        """Count files by extension"""
        counts = {}
        for file_path in self.files_found:
            ext = file_path.suffix.lower()
            counts[ext] = counts.get(ext, 0) + 1
        return counts
