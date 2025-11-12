# VMU Pro SD Save Importer

Automatically organize and import Dreamcast VMU save files for VMU Pro with OpenMenu support.

## Features

- **Automatic Scanning**: Recursively scans directories for .VMU, .VMS, and .DCI files
- **Game Detection**: Identifies games from save file metadata
- **OpenMenu Integration**: Uses OpenMenu's game database for accurate game identification
- **Channel Organization**: Organizes saves into VMU Pro's channel-based structure
- **Virtual VMU Creation**: Creates properly formatted virtual VMU files
- **Batch Processing**: Handles hundreds of saves automatically

## How It Works

1. **Scan**: Searches input directory for all VMU save files
2. **Parse**: Extracts game identification from each save file
3. **Identify**: Maps saves to games using OpenMenu database and metadata
4. **Organize**: Groups saves by game and creates channels
5. **Export**: Generates VMU Pro-compatible directory structure

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage
python vmupro_importer.py --input /path/to/messy/saves --output /path/to/sd/card

# With options
python vmupro_importer.py \
  --input /path/to/saves \
  --output /path/to/output \
  --max-channels 4 \
  --verbose
```

## Options

- `--input`: Source directory containing VMU files (required)
- `--output`: Output directory for VMU Pro structure (required)
- `--max-channels`: Maximum channels per game (default: 8)
- `--database`: Path to custom game database (optional)
- `--verbose`: Enable detailed logging
- `--dry-run`: Preview actions without making changes

## VMU Pro Structure

The tool creates the following structure compatible with VMU Pro:

```
/VMUPRO/
  /GAMES/
    /{GAME_ID}/
      /CHANNEL_1/
        SAVES/
          *.VMS
      /CHANNEL_2/
        SAVES/
          *.VMS
  /DATABASE/
    games.json
```

## Supported File Formats

- `.VMS` - Dreamcast save files
- `.VMU` - VMU dump files
- `.DCI` - DreamExplorer format
- `.BIN` - Raw VMU backups

## Requirements

- Python 3.8+
- vmu-tools library
- 8BitMods VMU Pro device (for actual use)

## License

MIT License

## Credits

- Built for 8BitMods VMU Pro
- Uses OpenMenu game database
- VMU parsing via vmu-tools library
