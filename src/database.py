"""
Game Database Manager
Manages Dreamcast game database for game identification
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class GameDatabase:
    """Manages game database for identifying saves"""

    def __init__(self, database_path: Optional[Path] = None):
        self.database_path = database_path or Path(__file__).parent.parent / 'data' / 'games.json'
        self.games = {}
        self.app_name_index = {}
        self.disc_id_index = {}

    def load(self):
        """Load game database from JSON"""
        try:
            if self.database_path.exists():
                logger.info(f"Loading database: {self.database_path}")
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.games = data.get('games', {})
                    self._build_indices()
                    logger.info(f"Loaded {len(self.games)} games")
            else:
                logger.warning(f"Database not found: {self.database_path}")
                logger.info("Using built-in game patterns")
                self._load_builtin_patterns()
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            self._load_builtin_patterns()

    def _build_indices(self):
        """Build search indices for fast lookup"""
        self.app_name_index = {}
        self.disc_id_index = {}

        for game_id, game_data in self.games.items():
            # Index by disc ID
            disc_ids = game_data.get('disc_ids', [])
            for disc_id in disc_ids:
                self.disc_id_index[disc_id.upper()] = game_id

            # Index by application names / save patterns
            app_names = game_data.get('app_names', [])
            for app_name in app_names:
                self.app_name_index[app_name.upper()] = game_id

    def _load_builtin_patterns(self):
        """Load built-in game identification patterns"""
        # Common Dreamcast game patterns based on research
        builtin = {
            "SONIC_ADVENTURE": {
                "title": "Sonic Adventure",
                "disc_ids": ["MK-51035", "HDR-0076"],
                "app_names": ["SONIC", "SONICADV"]
            },
            "SONIC_ADVENTURE_2": {
                "title": "Sonic Adventure 2",
                "disc_ids": ["MK-51166"],
                "app_names": ["SONIC2", "SA2"]
            },
            "SHENMUE": {
                "title": "Shenmue",
                "disc_ids": ["MK-51052"],
                "app_names": ["SHENMUE"]
            },
            "SHENMUE_II": {
                "title": "Shenmue II",
                "disc_ids": ["MK-51168"],
                "app_names": ["SHENMUE2"]
            },
            "SOUL_CALIBUR": {
                "title": "Soul Calibur",
                "disc_ids": ["T1203N"],
                "app_names": ["SCALIBUR", "SOULCALIBUR"]
            },
            "CRAZY_TAXI": {
                "title": "Crazy Taxi",
                "disc_ids": ["T-8107N"],
                "app_names": ["CRAZYTAXI", "CRAZY"]
            },
            "JET_GRIND_RADIO": {
                "title": "Jet Grind Radio",
                "disc_ids": ["MK-51058"],
                "app_names": ["JETGRIND", "JSR"]
            },
            "POWERSTONE": {
                "title": "Power Stone",
                "disc_ids": ["T-1211N"],
                "app_names": ["POWERSTONE"]
            },
            "POWERSTONE_2": {
                "title": "Power Stone 2",
                "disc_ids": ["T-1218N"],
                "app_names": ["POWERSTONE2", "PS2"]
            },
            "RESIDENT_EVIL_CODE_VERONICA": {
                "title": "Resident Evil Code: Veronica",
                "disc_ids": ["T-1204N"],
                "app_names": ["BIOHAZARD", "REHCV"]
            },
            "MARVEL_VS_CAPCOM_2": {
                "title": "Marvel vs Capcom 2",
                "disc_ids": ["T-1222N"],
                "app_names": ["MVC2", "MARVEL"]
            },
            "VIRTUAL_TENNIS": {
                "title": "Virtua Tennis",
                "disc_ids": ["MK-51044"],
                "app_names": ["VTENN", "VIRTUA_TENNIS"]
            }
        }

        self.games = builtin
        self._build_indices()
        logger.info(f"Loaded {len(builtin)} built-in game patterns")

    def identify_game(self, save_data: Dict) -> Optional[str]:
        """
        Identify game from save data

        Args:
            save_data: Parsed save metadata

        Returns:
            Game ID string, or None if not identified
        """
        # Strategy 1: Try application name from header
        app_name = save_data.get('application', '').upper().strip()
        if app_name:
            # Direct match
            if app_name in self.app_name_index:
                game_id = self.app_name_index[app_name]
                logger.debug(f"Identified by app name: {app_name} -> {game_id}")
                return game_id

            # Partial match
            for pattern, game_id in self.app_name_index.items():
                if pattern in app_name or app_name in pattern:
                    logger.debug(f"Identified by partial match: {app_name} -> {game_id}")
                    return game_id

        # Strategy 2: Try description text
        description = save_data.get('description', '').upper().strip()
        if description:
            for pattern, game_id in self.app_name_index.items():
                if pattern in description:
                    logger.debug(f"Identified by description: {description} -> {game_id}")
                    return game_id

        # Strategy 3: Try filename
        filename = save_data.get('file_name', '').upper()
        for pattern, game_id in self.app_name_index.items():
            if pattern in filename:
                logger.debug(f"Identified by filename: {filename} -> {game_id}")
                return game_id

        # Strategy 4: Generate ID from application name
        if app_name:
            # Clean and normalize application name
            game_id = self._generate_game_id(app_name)
            logger.debug(f"Generated ID from app name: {app_name} -> {game_id}")
            return game_id

        # Strategy 5: Use filename as fallback
        if filename:
            game_id = self._generate_game_id(filename.replace('.VMS', '').replace('.VMU', ''))
            logger.debug(f"Generated ID from filename: {filename} -> {game_id}")
            return game_id

        logger.warning(f"Could not identify game for: {save_data.get('file_name')}")
        return "UNKNOWN"

    def _generate_game_id(self, name: str) -> str:
        """Generate a game ID from a name"""
        # Remove special characters and normalize
        clean = re.sub(r'[^A-Z0-9_]', '_', name.upper())
        clean = re.sub(r'_+', '_', clean).strip('_')
        return clean[:32]  # Limit length

    def get_game_info(self, game_id: str) -> Dict:
        """Get game information by ID"""
        return self.games.get(game_id, {
            'title': game_id.replace('_', ' ').title(),
            'disc_ids': [],
            'app_names': []
        })

    def game_count(self) -> int:
        """Get number of games in database"""
        return len(self.games)

    def export_database(self, output_path: Path):
        """Export current database to JSON"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({'games': self.games}, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported database to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export database: {e}")
