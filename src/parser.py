"""
VMU File Parser
Parses VMU files and extracts save metadata
"""

import logging
import struct
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VMUParser:
    """Parses VMU save files and extracts metadata"""

    def __init__(self):
        self.parsed_count = 0

    def parse(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a VMU file and extract metadata

        Args:
            file_path: Path to VMU file

        Returns:
            Dictionary containing save metadata, or None if parsing fails
        """
        try:
            logger.debug(f"Parsing: {file_path}")

            # Determine file type and parse accordingly
            ext = file_path.suffix.lower()

            if ext in ['.vms', '.vmu']:
                return self._parse_vms(file_path)
            elif ext == '.dci':
                return self._parse_dci(file_path)
            elif ext == '.bin':
                return self._parse_vmu_dump(file_path)
            else:
                logger.warning(f"Unknown file type: {ext}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    def _parse_vms(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse VMS (single save) file

        VMS File Structure:
        - VMS files contain save data with a header
        - Header at offset 0 for data files, offset 0x200 for game files
        - Header contains: VMU description, copyright, creation date, etc.
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            if len(data) < 108:  # Minimum size for valid VMS
                logger.warning(f"File too small: {file_path}")
                return None

            # Try parsing header at offset 0 first (data file)
            header = self._parse_vms_header(data, 0)

            # If that fails, try offset 0x200 (game file)
            if not header or not header.get('valid'):
                header = self._parse_vms_header(data, 0x200)

            if not header or not header.get('valid'):
                logger.warning(f"Could not find valid header: {file_path}")
                # Still try to extract basic info from filename
                header = self._parse_from_filename(file_path)

            # Add file information
            header['file_path'] = str(file_path)
            header['file_size'] = len(data)
            header['file_name'] = file_path.name
            header['raw_data'] = data

            self.parsed_count += 1
            return header

        except Exception as e:
            logger.error(f"Error parsing VMS {file_path}: {e}")
            return None

    def _parse_vms_header(self, data: bytes, offset: int) -> Dict[str, Any]:
        """
        Parse VMS header at given offset

        Header structure (128 bytes):
        0x00-0x0F: VM description (16 bytes) - describes the file
        0x10-0x1F: Copyright info (32 bytes)
        0x40: Year (BCD, 2 bytes for century + year)
        0x42: Month (BCD)
        0x43: Day (BCD)
        0x44: Hour (BCD)
        0x45: Minute (BCD)
        0x46: Second (BCD)
        0x47: Day of week (BCD)
        0x48-0x49: VMU description icon palette (2 bytes)
        0x4A-0x4B: Number of icon frames (2 bytes, little endian)
        0x4C-0x4D: Animation speed (2 bytes, little endian)
        0x4E-0x4F: Eye-catch type (2 bytes)
        0x50-0x51: CRC (2 bytes, little endian)
        0x52-0x55: Data size (4 bytes, little endian)
        ...
        0x70-0x7F: Application name (16 bytes) - IMPORTANT for game ID
        """
        try:
            if offset + 128 > len(data):
                return {'valid': False}

            header = {}

            # Extract VM description (0x00-0x0F)
            desc_bytes = data[offset:offset+16]
            header['description'] = self._clean_string(desc_bytes)

            # Extract copyright (0x10-0x2F)
            copyright_bytes = data[offset+0x10:offset+0x30]
            header['copyright'] = self._clean_string(copyright_bytes)

            # Extract application name (0x70-0x7F) - Critical for game identification
            app_bytes = data[offset+0x70:offset+0x80]
            header['application'] = self._clean_string(app_bytes)

            # Try to extract date (BCD format at 0x40-0x47)
            try:
                year = self._bcd_to_int(data[offset+0x41]) + (self._bcd_to_int(data[offset+0x40]) * 100)
                month = self._bcd_to_int(data[offset+0x42])
                day = self._bcd_to_int(data[offset+0x43])
                hour = self._bcd_to_int(data[offset+0x44])
                minute = self._bcd_to_int(data[offset+0x45])
                second = self._bcd_to_int(data[offset+0x46])

                if 1990 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    header['timestamp'] = datetime(year, month, day, hour, minute, second)
                else:
                    header['timestamp'] = None
            except:
                header['timestamp'] = None

            # Extract file size (0x52-0x55)
            try:
                file_size = struct.unpack('<I', data[offset+0x52:offset+0x56])[0]
                header['save_size'] = file_size
            except:
                header['save_size'] = len(data)

            # Mark as valid if we got meaningful data
            header['valid'] = bool(header['description'] or header['application'])

            return header

        except Exception as e:
            logger.debug(f"Failed to parse header at offset {offset}: {e}")
            return {'valid': False}

    def _parse_dci(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse DCI (Nexus DC) format"""
        # DCI format is similar to VMS but with additional wrapper
        # For now, treat as VMS after header
        return self._parse_vms(file_path)

    def _parse_vmu_dump(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse complete VMU dump file (128KB)

        VMU dumps contain:
        - 256 blocks of 512 bytes each
        - Directory at blocks 241-253
        - FAT at block 254
        - Root at block 255
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            if len(data) != 131072:  # 128KB exact
                logger.warning(f"VMU dump wrong size: {len(data)} bytes")
                return None

            # For VMU dumps, we need to extract individual saves
            # This is complex, so for now return basic dump info
            return {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': len(data),
                'type': 'vmu_dump',
                'description': f'VMU Dump: {file_path.stem}',
                'application': 'VMU_DUMP',
                'valid': True,
                'raw_data': data
            }

        except Exception as e:
            logger.error(f"Error parsing VMU dump {file_path}: {e}")
            return None

    def _parse_from_filename(self, file_path: Path) -> Dict[str, Any]:
        """Extract info from filename when header parsing fails"""
        return {
            'description': file_path.stem,
            'application': file_path.stem.upper()[:16],
            'copyright': '',
            'timestamp': None,
            'valid': True
        }

    def _clean_string(self, data: bytes) -> str:
        """Clean and decode string from bytes"""
        # Try multiple encodings
        for encoding in ['ascii', 'shift_jis', 'utf-8', 'latin1']:
            try:
                # Remove null bytes and control characters
                cleaned = data.split(b'\x00')[0]
                text = cleaned.decode(encoding).strip()
                # Remove non-printable characters
                text = ''.join(c for c in text if c.isprintable() or c.isspace())
                if text:
                    return text
            except:
                continue
        return ''

    def _bcd_to_int(self, bcd: int) -> int:
        """Convert BCD (Binary Coded Decimal) to integer"""
        return ((bcd >> 4) * 10) + (bcd & 0x0F)

    def get_statistics(self) -> dict:
        """Get parsing statistics"""
        return {
            'parsed_count': self.parsed_count
        }
