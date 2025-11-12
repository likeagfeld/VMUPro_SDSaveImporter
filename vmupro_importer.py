#!/usr/bin/env python3
"""
VMU Pro SD Save Importer
Automatically organize Dreamcast VMU saves for VMU Pro with OpenMenu support
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from colorama import init, Fore, Style
from tqdm import tqdm

from src.scanner import VMUScanner
from src.parser import VMUParser
from src.database import GameDatabase
from src.organizer import SaveOrganizer
from src.writer import VMUProWriter

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vmupro_importer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VMUProImporter:
    """Main application class for VMU Pro SD Save Importer"""

    def __init__(self, input_path: Path, output_path: Path,
                 max_channels: int = 8, database_path: Optional[Path] = None,
                 verbose: bool = False, dry_run: bool = False):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.max_channels = max_channels
        self.verbose = verbose
        self.dry_run = dry_run

        # Initialize components
        self.scanner = VMUScanner()
        self.parser = VMUParser()
        self.database = GameDatabase(database_path)
        self.organizer = SaveOrganizer(max_channels)
        self.writer = VMUProWriter(output_path, dry_run)

        if verbose:
            logger.setLevel(logging.DEBUG)

    def run(self):
        """Execute the import process"""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}VMU Pro SD Save Importer")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        try:
            # Step 1: Scan for VMU files
            print(f"{Fore.YELLOW}[1/5] Scanning for VMU files...{Style.RESET_ALL}")
            vmu_files = self.scanner.scan(self.input_path)
            print(f"{Fore.GREEN}✓ Found {len(vmu_files)} VMU files{Style.RESET_ALL}\n")

            if len(vmu_files) == 0:
                print(f"{Fore.RED}No VMU files found in {self.input_path}{Style.RESET_ALL}")
                return

            # Step 2: Parse VMU files
            print(f"{Fore.YELLOW}[2/5] Parsing VMU files...{Style.RESET_ALL}")
            parsed_saves = []
            for vmu_file in tqdm(vmu_files, desc="Parsing", unit="file"):
                try:
                    save_data = self.parser.parse(vmu_file)
                    if save_data:
                        parsed_saves.append(save_data)
                except Exception as e:
                    logger.warning(f"Failed to parse {vmu_file}: {e}")

            print(f"{Fore.GREEN}✓ Successfully parsed {len(parsed_saves)} saves{Style.RESET_ALL}\n")

            # Step 3: Load game database
            print(f"{Fore.YELLOW}[3/5] Loading game database...{Style.RESET_ALL}")
            self.database.load()
            print(f"{Fore.GREEN}✓ Loaded {self.database.game_count()} games{Style.RESET_ALL}\n")

            # Step 4: Identify and organize saves
            print(f"{Fore.YELLOW}[4/5] Identifying games and organizing saves...{Style.RESET_ALL}")
            organized = self.organizer.organize(parsed_saves, self.database)
            game_count = len(organized)
            save_count = sum(len(channels) for channels in organized.values())
            print(f"{Fore.GREEN}✓ Organized {save_count} saves across {game_count} games{Style.RESET_ALL}\n")

            # Step 5: Write VMU Pro structure
            print(f"{Fore.YELLOW}[5/5] Creating VMU Pro structure...{Style.RESET_ALL}")
            if self.dry_run:
                print(f"{Fore.CYAN}[DRY RUN] Would create:{Style.RESET_ALL}")
                self.writer.preview(organized)
            else:
                self.writer.write(organized)
                print(f"{Fore.GREEN}✓ Successfully created VMU Pro structure{Style.RESET_ALL}\n")

            # Summary
            print(f"\n{Fore.CYAN}{'='*70}")
            print(f"{Fore.GREEN}Import Complete!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"  Total files processed: {len(vmu_files)}")
            print(f"  Saves organized: {len(parsed_saves)}")
            print(f"  Games identified: {game_count}")
            if not self.dry_run:
                print(f"  Output directory: {self.output_path}")
            print()

        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Import cancelled by user{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            print(f"\n{Fore.RED}✗ Import failed: {e}{Style.RESET_ALL}")
            sys.exit(1)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VMU Pro SD Save Importer - Organize Dreamcast saves for VMU Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic import
  python vmupro_importer.py --input /mnt/sdcard --output /mnt/vmupro

  # Preview changes without writing
  python vmupro_importer.py --input ./saves --output ./output --dry-run

  # With custom settings
  python vmupro_importer.py -i ./saves -o ./output --max-channels 4 --verbose
        """
    )

    parser.add_argument('-i', '--input', required=True, type=Path,
                        help='Input directory containing VMU files')
    parser.add_argument('-o', '--output', required=True, type=Path,
                        help='Output directory for VMU Pro structure')
    parser.add_argument('--max-channels', type=int, default=8,
                        help='Maximum channels per game (default: 8)')
    parser.add_argument('--database', type=Path,
                        help='Path to custom game database JSON')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing files')

    args = parser.parse_args()

    # Validate input path
    if not args.input.exists():
        print(f"{Fore.RED}Error: Input path does not exist: {args.input}{Style.RESET_ALL}")
        sys.exit(1)

    # Create output directory if needed
    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    # Run importer
    importer = VMUProImporter(
        input_path=args.input,
        output_path=args.output,
        max_channels=args.max_channels,
        database_path=args.database,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    importer.run()


if __name__ == '__main__':
    main()
