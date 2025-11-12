"""
VMU Pro Structure Writer
Creates VMU Pro-compatible directory structure
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VMUProWriter:
    """Writes organized saves to VMU Pro directory structure"""

    def __init__(self, output_path: Path, dry_run: bool = False):
        self.output_path = Path(output_path)
        self.dry_run = dry_run
        self.files_written = 0
        self.bytes_written = 0

    def write(self, organized: Dict[str, List[List[Dict]]]):
        """
        Write organized saves to VMU Pro structure

        VMU Pro Structure (based on research and similar devices):
        /VMUPRO/
          /GAMES/
            /{GAME_ID}/
              game_info.json
              /CHANNEL_1/
                /SAVES/
                  save1.vms
                  save2.vms
              /CHANNEL_2/
                /SAVES/
                  save3.vms
          /DATABASE/
            games.json
            import_log.json

        Args:
            organized: Dictionary of organized saves by game and channel
        """
        logger.info(f"Writing VMU Pro structure to: {self.output_path}")

        try:
            # Create base directories
            self._create_base_structure()

            # Write each game's saves
            game_database = {}

            for game_id, channels in organized.items():
                game_info = self._write_game(game_id, channels)
                game_database[game_id] = game_info

            # Write database files
            self._write_database(game_database)

            # Write import log
            self._write_import_log(organized)

            logger.info(f"Successfully wrote {self.files_written} files ({self.bytes_written} bytes)")

        except Exception as e:
            logger.error(f"Failed to write VMU Pro structure: {e}")
            raise

    def _create_base_structure(self):
        """Create base directory structure"""
        dirs = [
            self.output_path / 'VMUPRO',
            self.output_path / 'VMUPRO' / 'GAMES',
            self.output_path / 'VMUPRO' / 'DATABASE'
        ]

        for dir_path in dirs:
            if not self.dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

    def _write_game(self, game_id: str, channels: List[List[Dict]]) -> Dict:
        """
        Write a game's saves to channels

        Args:
            game_id: Game identifier
            channels: List of channels, each containing saves

        Returns:
            Game info dictionary
        """
        game_dir = self.output_path / 'VMUPRO' / 'GAMES' / game_id

        if not self.dry_run:
            game_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing game: {game_id} ({len(channels)} channels)")

        # Collect game metadata from first save
        first_save = channels[0][0] if channels and channels[0] else {}
        game_info = {
            'game_id': game_id,
            'title': first_save.get('description', game_id.replace('_', ' ').title()),
            'channel_count': len(channels),
            'total_saves': sum(len(ch) for ch in channels),
            'created': datetime.now().isoformat()
        }

        # Write each channel
        for channel_idx, channel_saves in enumerate(channels, start=1):
            self._write_channel(game_dir, channel_idx, channel_saves, game_id)

        # Write game info
        game_info_path = game_dir / 'game_info.json'
        if not self.dry_run:
            with open(game_info_path, 'w', encoding='utf-8') as f:
                json.dump(game_info, f, indent=2, ensure_ascii=False)
        self.files_written += 1

        return game_info

    def _write_channel(self, game_dir: Path, channel_num: int,
                       saves: List[Dict], game_id: str):
        """
        Write a channel's saves

        Args:
            game_dir: Game directory path
            channel_num: Channel number (1-indexed)
            saves: List of save data for this channel
            game_id: Game identifier
        """
        channel_dir = game_dir / f'CHANNEL_{channel_num}'
        saves_dir = channel_dir / 'SAVES'

        if not self.dry_run:
            saves_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"  Channel {channel_num}: {len(saves)} saves")

        # Write channel metadata
        channel_info = {
            'channel_number': channel_num,
            'game_id': game_id,
            'save_count': len(saves),
            'saves': []
        }

        # Write each save file
        for save_idx, save in enumerate(saves, start=1):
            save_info = self._write_save(saves_dir, save, save_idx)
            channel_info['saves'].append(save_info)

        # Write channel info
        channel_info_path = channel_dir / 'channel_info.json'
        if not self.dry_run:
            with open(channel_info_path, 'w', encoding='utf-8') as f:
                json.dump(channel_info, f, indent=2, ensure_ascii=False)
        self.files_written += 1

    def _write_save(self, saves_dir: Path, save: Dict, save_num: int) -> Dict:
        """
        Write a single save file

        Args:
            saves_dir: Directory to write save
            save: Save data dictionary
            save_num: Save number for naming

        Returns:
            Save info dictionary
        """
        # Determine output filename
        original_name = save.get('file_name', f'save_{save_num}.vms')
        output_name = self._sanitize_filename(original_name)

        # Ensure .vms extension
        if not output_name.lower().endswith('.vms'):
            output_name = output_name.rsplit('.', 1)[0] + '.vms'

        output_path = saves_dir / output_name

        # Copy save data
        if not self.dry_run:
            raw_data = save.get('raw_data')
            if raw_data:
                with open(output_path, 'wb') as f:
                    f.write(raw_data)
                self.bytes_written += len(raw_data)
            else:
                # Copy from source file
                source_path = Path(save['file_path'])
                shutil.copy2(source_path, output_path)
                self.bytes_written += source_path.stat().st_size

        self.files_written += 1

        # Return save info
        return {
            'filename': output_name,
            'original_path': save.get('file_path', ''),
            'description': save.get('description', ''),
            'application': save.get('application', ''),
            'size': save.get('file_size', 0),
            'timestamp': save.get('timestamp').isoformat() if save.get('timestamp') else None
        }

    def _write_database(self, game_database: Dict):
        """Write games database"""
        db_path = self.output_path / 'VMUPRO' / 'DATABASE' / 'games.json'

        database = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'game_count': len(game_database),
            'games': game_database
        }

        if not self.dry_run:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
        self.files_written += 1

        logger.info(f"Wrote game database: {len(game_database)} games")

    def _write_import_log(self, organized: Dict):
        """Write import log for reference"""
        log_path = self.output_path / 'VMUPRO' / 'DATABASE' / 'import_log.json'

        log_data = {
            'import_date': datetime.now().isoformat(),
            'total_games': len(organized),
            'total_channels': sum(len(channels) for channels in organized.values()),
            'total_saves': sum(
                sum(len(channel) for channel in channels)
                for channels in organized.values()
            ),
            'files_written': self.files_written,
            'bytes_written': self.bytes_written
        }

        if not self.dry_run:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info("Wrote import log")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:50]  # Limit name length

        return f"{name}.{ext}" if ext else name

    def preview(self, organized: Dict):
        """Preview what would be written (for dry-run)"""
        print("\nWould create the following structure:\n")

        print("VMUPRO/")
        print("  DATABASE/")
        print("    games.json")
        print("    import_log.json")
        print("  GAMES/")

        for game_id, channels in organized.items():
            print(f"    {game_id}/")
            print(f"      game_info.json")

            for channel_idx, channel_saves in enumerate(channels, start=1):
                print(f"      CHANNEL_{channel_idx}/")
                print(f"        channel_info.json")
                print(f"        SAVES/")

                for save in channel_saves[:3]:  # Show first 3 saves
                    filename = save.get('file_name', 'unknown')
                    print(f"          {filename}")

                if len(channel_saves) > 3:
                    print(f"          ... and {len(channel_saves) - 3} more saves")

        print("\nSummary:")
        print(f"  Games: {len(organized)}")
        print(f"  Channels: {sum(len(ch) for ch in organized.values())}")
        print(f"  Saves: {sum(sum(len(c) for c in ch) for ch in organized.values())}")
