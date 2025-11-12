# VMU Pro SD Save Importer - Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Options](#advanced-options)
5. [Understanding the Output](#understanding-the-output)
6. [Troubleshooting](#troubleshooting)
7. [Adding Custom Games](#adding-custom-games)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the importer
python vmupro_importer.py --input /path/to/messy/saves --output /path/to/sd/card
```

## Installation

### Requirements
- Python 3.8 or higher
- VMU Pro device (for actual use)
- SD card formatted for VMU Pro

### Steps

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python vmupro_importer.py --help
   ```

## Basic Usage

### Scenario 1: Import from a messy folder

You have a folder full of VMU files in various subdirectories:

```
/my_saves/
  random_file.vms
  sonic/
    save1.vms
    save2.vms
  old_backups/
    shenmue.vmu
    more_saves/
      ...
```

Run:
```bash
python vmupro_importer.py --input /my_saves --output /mnt/sdcard/VMUPRO
```

### Scenario 2: Preview before importing (Dry Run)

To see what the tool will do without actually writing files:

```bash
python vmupro_importer.py --input ./saves --output ./test --dry-run
```

This shows you:
- How many files were found
- How games were identified
- How saves will be organized
- The directory structure that would be created

### Scenario 3: Import with custom settings

```bash
python vmupro_importer.py \
  --input /mnt/old_sd \
  --output /mnt/new_sd/VMUPRO \
  --max-channels 4 \
  --verbose
```

Options:
- `--max-channels 4`: Limit to 4 channels per game (default: 8)
- `--verbose`: Show detailed logging

## Advanced Options

### Custom Game Database

If you have your own game identification database:

```bash
python vmupro_importer.py \
  --input ./saves \
  --output ./output \
  --database ./my_custom_games.json
```

Database format:
```json
{
  "games": {
    "MY_GAME": {
      "title": "My Cool Game",
      "disc_ids": ["MK-12345"],
      "app_names": ["MYGAME", "MY_COOL"]
    }
  }
}
```

### Processing Large Collections

For thousands of saves:

1. **Use verbose mode** to monitor progress:
   ```bash
   python vmupro_importer.py -i ./saves -o ./output --verbose
   ```

2. **Check the log file** for details:
   ```bash
   tail -f vmupro_importer.log
   ```

3. **Process incrementally** if needed:
   ```bash
   # Process by game series
   python vmupro_importer.py -i ./saves/sonic -o ./output
   python vmupro_importer.py -i ./saves/capcom -o ./output
   ```

## Understanding the Output

### Directory Structure

The tool creates this structure on your SD card:

```
VMUPRO/
├── DATABASE/
│   ├── games.json          # Database of all imported games
│   └── import_log.json     # Import statistics and log
│
└── GAMES/
    ├── SONIC_ADVENTURE/
    │   ├── game_info.json
    │   ├── CHANNEL_1/
    │   │   ├── channel_info.json
    │   │   └── SAVES/
    │   │       ├── save1.vms
    │   │       └── save2.vms
    │   └── CHANNEL_2/
    │       └── SAVES/
    │           └── save3.vms
    │
    └── SHENMUE/
        └── CHANNEL_1/
            └── SAVES/
                ├── disc1.vms
                └── disc2.vms
```

### Channels

Each game can have multiple channels (like having multiple VMUs):
- **Channel 1**: Primary saves
- **Channel 2**: Additional saves (different character, new game+, etc.)
- **Channel 3+**: More save slots as needed

You can switch channels on VMU Pro while playing!

### Metadata Files

**game_info.json**: Information about the game
```json
{
  "game_id": "SONIC_ADVENTURE",
  "title": "Sonic Adventure",
  "channel_count": 2,
  "total_saves": 5
}
```

**channel_info.json**: Information about a specific channel
```json
{
  "channel_number": 1,
  "game_id": "SONIC_ADVENTURE",
  "save_count": 3,
  "saves": [...]
}
```

## Troubleshooting

### Issue: "No VMU files found"

**Causes:**
- Wrong input directory
- Files have wrong extension
- File sizes are invalid

**Solutions:**
1. Check the path: `ls /path/to/saves`
2. Look for these extensions: `.vmu`, `.vms`, `.dci`, `.bin`
3. Use verbose mode: `--verbose` to see what's being skipped

### Issue: "Could not identify game"

**Causes:**
- Save file has corrupted header
- Game not in database
- Non-standard save file

**Solutions:**
1. Check if the save appears under `UNKNOWN` game
2. Add the game to custom database
3. The file is still imported, just not automatically identified

### Issue: "Permission denied"

**Causes:**
- No write access to output directory
- SD card is read-only or full

**Solutions:**
1. Check permissions: `ls -la /mnt/sdcard`
2. Try with sudo if needed: `sudo python vmupro_importer.py ...`
3. Check SD card space: `df -h`

### Issue: "Import incomplete or crashed"

**Solutions:**
1. Check the log file: `vmupro_importer.log`
2. Try with verbose mode
3. Test with a small subset first
4. Report issues on GitHub

## Adding Custom Games

### Method 1: Edit games.json

Add your game to `data/games.json`:

```json
{
  "MY_HOMEBREW_GAME": {
    "title": "My Homebrew Game",
    "disc_ids": ["HB_MYGAME"],
    "app_names": ["MYGAME", "MY_HB"],
    "region": ["USA"]
  }
}
```

### Method 2: Use Custom Database

Create `my_games.json` and use `--database` option.

### Identifying Application Names

To find the app name for a save:

1. **Look at the filename** - often contains the game name
2. **Use a hex editor** - check offset 0x70 in the VMS file
3. **Check with verbose mode** - shows detected app names

Example with hexdump:
```bash
hexdump -C mysave.vms | head -20
```

Look around offset 0x70 for ASCII text.

## Tips and Best Practices

### 1. Always Test First
Run with `--dry-run` before actual import:
```bash
python vmupro_importer.py -i ./saves -o ./test --dry-run
```

### 2. Backup Your Saves
Keep original saves somewhere safe before importing.

### 3. Organize Source Files
Pre-organize by game if possible - makes troubleshooting easier.

### 4. Use Descriptive Channel Names
The tool auto-creates channels, but you can manually rename folders later.

### 5. Check Import Log
After import, review `VMUPRO/DATABASE/import_log.json` for statistics.

### 6. Update Game Database
Contribute game identifications back to the project!

## Examples

### Example 1: Simple Import
```bash
python vmupro_importer.py \
  --input ~/Downloads/dreamcast_saves \
  --output /mnt/sdcard/VMUPRO
```

### Example 2: Preview Large Collection
```bash
python vmupro_importer.py \
  --input /backup/all_saves \
  --output ./preview \
  --dry-run \
  --verbose
```

### Example 3: Import with Limits
```bash
python vmupro_importer.py \
  --input ./saves \
  --output /mnt/vmupro \
  --max-channels 2  # Only 2 channels per game
```

### Example 4: Custom Database
```bash
python vmupro_importer.py \
  --input ./saves \
  --output ./output \
  --database ./homebrew_games.json
```

## Getting Help

- **Documentation**: Check README.md and this file
- **Issues**: Report on GitHub Issues
- **Community**: Join 8BitMods Discord
- **Logs**: Always include `vmupro_importer.log` when reporting issues

## Next Steps

After successful import:
1. Safely eject SD card
2. Insert into VMU Pro
3. Power on VMU Pro
4. Navigate to game saves
5. Enjoy automatic game detection with OpenMenu!
