"""
Save Organizer
Organizes saves by game and creates channel structure
"""

import logging
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class SaveOrganizer:
    """Organizes saves into VMU Pro channel structure"""

    def __init__(self, max_channels: int = 8):
        self.max_channels = max_channels

    def organize(self, saves: List[Dict[str, Any]], database) -> Dict[str, List[List[Dict]]]:
        """
        Organize saves by game and channel

        Args:
            saves: List of parsed save data
            database: GameDatabase instance

        Returns:
            Dictionary mapping game_id to list of channels, where each channel
            is a list of saves
            {
                'SONIC_ADVENTURE': [
                    [save1, save2],  # Channel 1
                    [save3],          # Channel 2
                ],
                'SHENMUE': [
                    [save4, save5, save6]  # Channel 1
                ]
            }
        """
        logger.info("Organizing saves by game...")

        # Group saves by game
        game_saves = defaultdict(list)

        for save in saves:
            game_id = database.identify_game(save)
            if game_id:
                game_saves[game_id].append(save)

        # Organize into channels
        organized = {}

        for game_id, save_list in game_saves.items():
            game_info = database.get_game_info(game_id)
            logger.info(f"Organizing {len(save_list)} saves for {game_info.get('title', game_id)}")

            # Sort saves by timestamp if available
            save_list.sort(key=lambda s: s.get('timestamp') or '', reverse=False)

            # Create channels
            channels = self._create_channels(save_list, game_id)
            organized[game_id] = channels

        logger.info(f"Organized {len(saves)} saves across {len(organized)} games")
        return organized

    def _create_channels(self, saves: List[Dict], game_id: str) -> List[List[Dict]]:
        """
        Create channels for a game's saves

        VMU Pro allows multiple channels per game. Each channel acts like
        a separate VMU with its own saves. This is useful for:
        - Multiple save slots
        - Different players
        - Different playthroughs

        Strategy:
        - Group similar saves together (by description/filename patterns)
        - Distribute saves across channels to avoid overcrowding
        - Respect max_channels limit
        """
        if not saves:
            return []

        # For now, use simple distribution strategy
        # Future: Could implement smart grouping by save slot, character, etc.

        channels = []
        saves_per_channel = self._calculate_saves_per_channel(len(saves))

        current_channel = []
        for i, save in enumerate(saves):
            current_channel.append(save)

            # Start new channel if current is full
            if len(current_channel) >= saves_per_channel:
                if len(channels) < self.max_channels - 1:  # Save room for last channel
                    channels.append(current_channel)
                    current_channel = []

        # Add remaining saves to last channel
        if current_channel:
            channels.append(current_channel)

        logger.debug(f"{game_id}: Created {len(channels)} channels")
        return channels

    def _calculate_saves_per_channel(self, total_saves: int) -> int:
        """
        Calculate optimal saves per channel

        VMU has 200 blocks available. Most saves are 1-20 blocks.
        Conservatively, allow ~10-20 saves per channel.
        """
        if total_saves <= self.max_channels:
            return 1  # One save per channel

        # Distribute evenly
        saves_per_channel = (total_saves + self.max_channels - 1) // self.max_channels

        # Cap at reasonable limit
        return min(saves_per_channel, 20)

    def get_statistics(self, organized: Dict) -> Dict:
        """Get organization statistics"""
        total_games = len(organized)
        total_channels = sum(len(channels) for channels in organized.values())
        total_saves = sum(
            sum(len(channel) for channel in channels)
            for channels in organized.values()
        )

        games_with_multi_channel = sum(
            1 for channels in organized.values() if len(channels) > 1
        )

        return {
            'total_games': total_games,
            'total_channels': total_channels,
            'total_saves': total_saves,
            'games_with_multiple_channels': games_with_multi_channel,
            'avg_saves_per_game': total_saves / total_games if total_games > 0 else 0,
            'avg_channels_per_game': total_channels / total_games if total_games > 0 else 0
        }
