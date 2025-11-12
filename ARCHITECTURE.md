# VMU Pro SD Save Importer - Architecture

## Overview

This document describes the architecture, design decisions, and implementation details of the VMU Pro SD Save Importer.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VMU Pro Importer                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐         │
│  │ Scanner  │───>│  Parser  │───>│  Database    │         │
│  └──────────┘    └──────────┘    └──────────────┘         │
│       │               │                  │                  │
│       v               v                  v                  │
│  ┌─────────────────────────────────────────────┐           │
│  │           Organizer                         │           │
│  │  (Groups saves by game + channels)         │           │
│  └─────────────────────────────────────────────┘           │
│                      │                                      │
│                      v                                      │
│  ┌─────────────────────────────────────────────┐           │
│  │           Writer                            │           │
│  │  (Creates VMU Pro structure)               │           │
│  └─────────────────────────────────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### 1. Scanner (`src/scanner.py`)

**Purpose**: Recursively scan directories for VMU save files

**Key Features**:
- Supports multiple file extensions: `.vmu`, `.vms`, `.dci`, `.bin`
- File size validation (512 bytes to 128KB)
- Recursive directory traversal
- Permission error handling

**Algorithm**:
1. Start at input directory
2. For each item:
   - If file: check if valid VMU file
   - If directory: recurse
3. Return sorted list of file paths

**Performance**: O(n) where n = number of files in tree

### 2. Parser (`src/parser.py`)

**Purpose**: Parse VMU files and extract metadata

**Supported Formats**:
- **VMS**: Single save files
- **VMI**: Metadata files (companion to VMS)
- **DCI**: Nexus DC format
- **BIN**: Complete VMU dumps (128KB)

**VMS Header Structure** (Critical for game identification):
```
Offset  Size  Field
------  ----  -----
0x00    16    VM Description
0x10    32    Copyright
0x40    8     Timestamp (BCD)
0x52    4     File size
0x70    16    Application name ← CRITICAL for game ID!
```

**Parsing Strategy**:
1. Read file data
2. Try header at offset 0x00 (data files)
3. If fails, try offset 0x200 (game files)
4. Extract all metadata fields
5. Clean and normalize strings

**Fallbacks**:
- If header parsing fails: extract info from filename
- If encoding fails: try multiple encodings (ASCII, Shift-JIS, UTF-8)
- If timestamp invalid: set to None

### 3. Database (`src/database.py`)

**Purpose**: Identify games from save file metadata

**Data Structure**:
```json
{
  "GAME_ID": {
    "title": "Game Title",
    "disc_ids": ["MK-12345", "..."],
    "app_names": ["APPNAME", "ALT_NAME"]
  }
}
```

**Indices**:
- `disc_id_index`: Map disc ID → game ID
- `app_name_index`: Map application name → game ID

**Identification Strategy** (in priority order):
1. **Direct app name match**: Exact match on application name
2. **Partial app name match**: Substring matching
3. **Description match**: Search in save description
4. **Filename match**: Pattern matching in filename
5. **Generate ID**: Create ID from application name
6. **Fallback**: Use "UNKNOWN"

**Built-in Database**:
- 30+ popular Dreamcast games included
- Covers major franchises: Sonic, Shenmue, Capcom fighters, etc.
- User can provide custom database via `--database`

### 4. Organizer (`src/organizer.py`)

**Purpose**: Organize saves into game/channel structure

**Channel Concept**:
- VMU Pro supports multiple "channels" per game
- Each channel = virtual VMU with independent saves
- Switch channels on-device while playing
- Useful for: multiple save slots, different players, multiple playthroughs

**Organization Algorithm**:
```python
for each save:
    game_id = identify_game(save)
    add_to_game_saves[game_id]

for each game:
    saves = sort_by_timestamp(game_saves)
    channels = distribute_across_channels(saves)
```

**Distribution Strategy**:
- Calculate `saves_per_channel = total_saves / max_channels`
- Cap at 20 saves/channel (VMU has ~200 blocks, saves are 1-20 blocks)
- Future: Smart grouping by save slot numbers, character names, etc.

**Sorting**:
- Primary: By timestamp (oldest first)
- Secondary: By filename

### 5. Writer (`src/writer.py`)

**Purpose**: Write organized saves to VMU Pro directory structure

**Output Structure**:
```
VMUPRO/
├── DATABASE/
│   ├── games.json          # Master game database
│   └── import_log.json     # Import statistics
└── GAMES/
    └── {GAME_ID}/
        ├── game_info.json      # Game metadata
        └── CHANNEL_{N}/
            ├── channel_info.json   # Channel metadata
            └── SAVES/
                └── *.vms          # Save files
```

**File Operations**:
1. Create directory structure
2. Copy/write save files
3. Generate metadata JSON files
4. Write master database
5. Write import log

**Safety Features**:
- Dry-run mode (preview without writing)
- Filename sanitization
- Directory creation with error handling
- Atomic writes where possible

## Data Flow

### Complete Flow Example

```
Input: /messy_saves/sonic1.vms

1. Scanner:
   → Found: /messy_saves/sonic1.vms
   → Size: 5120 bytes ✓
   → Extension: .vms ✓

2. Parser:
   → Read file data
   → Parse header at offset 0x00
   → Extract: application="SONIC", description="SONIC ADV"
   → Return: {application: "SONIC", ...}

3. Database:
   → Lookup "SONIC" in app_name_index
   → Match: SONIC_ADVENTURE
   → Return: "SONIC_ADVENTURE"

4. Organizer:
   → Add to game_saves["SONIC_ADVENTURE"]
   → After all files: Create 1 channel with 1 save

5. Writer:
   → Create: VMUPRO/GAMES/SONIC_ADVENTURE/
   → Create: CHANNEL_1/SAVES/
   → Copy: sonic1.vms
   → Write: metadata JSONs
```

## Design Decisions

### Why Python?
- Cross-platform (Windows, Mac, Linux)
- Rich ecosystem for file operations
- Easy to extend and modify
- Good libraries available (vmu-tools)

### Why JSON for metadata?
- Human-readable
- Easy to parse
- Cross-platform compatible
- Future-proof (easy to extend schema)

### Why channel-based organization?
- Mirrors VMU Pro's native functionality
- Flexible: supports any number of saves per game
- User can switch channels on-device
- Prevents VMU from filling up (distribute across channels)

### Why built-in game database?
- Works out-of-box for common games
- Reduces dependency on external resources
- Users can extend with custom database

## Error Handling

### Strategy: Graceful degradation

1. **File access errors**: Log warning, continue with other files
2. **Parse errors**: Log warning, attempt filename extraction
3. **Identification failures**: Mark as "UNKNOWN", still import
4. **Write errors**: Fail fast, log details

### Logging Levels

- **DEBUG**: Detailed parsing info, file operations
- **INFO**: Progress updates, statistics
- **WARNING**: Non-critical failures (skipped files)
- **ERROR**: Critical failures that stop import

## Performance Considerations

### Time Complexity
- Scanning: O(n) - n = files in directory tree
- Parsing: O(m) - m = number of VMU files
- Identification: O(1) with indices
- Organization: O(m log m) - sorting saves
- Writing: O(m) - copying files

### Memory Usage
- Loads full save data into memory during processing
- For large collections (1000s of saves):
  - Peak memory: ~500MB-1GB
  - Streaming: Future optimization if needed

### Disk I/O
- Reads: One read per save file
- Writes: One write per save + metadata
- Optimization: Bulk operations where possible

## Future Enhancements

### Planned Features

1. **VMU-tools Integration**
   - Use vmu-tools library for advanced parsing
   - Extract icon images
   - Validate checksums

2. **Smart Channel Organization**
   - Detect save slot numbers (File 1, File 2, etc.)
   - Group by character/campaign
   - User-defined channel naming

3. **OpenMenu Integration**
   - Fetch OpenMenu game database
   - Map disc IDs to game metadata
   - Download box art

4. **GUI Version**
   - Drag-and-drop interface
   - Visual progress
   - Preview structure before import

5. **Incremental Import**
   - Detect existing imports
   - Only add new saves
   - Update channel organization

6. **Save Management**
   - Merge multiple imports
   - Deduplicate saves
   - Sort/reorganize existing structure

7. **VMU Dump Extraction**
   - Parse complete VMU dumps
   - Extract individual saves from dump
   - Preserve directory structure

## Testing Strategy

### Test Levels

1. **Unit Tests**: Each module independently
   - Scanner: Find various file types
   - Parser: Handle valid/invalid headers
   - Database: Identify known/unknown games
   - Organizer: Create proper channels
   - Writer: Generate correct structure

2. **Integration Tests**: Full workflow
   - Import small collection
   - Import large collection
   - Handle corrupted files
   - Verify output structure

3. **Validation Tests**: Output correctness
   - Verify metadata accuracy
   - Check file integrity
   - Validate JSON schema

### Test Data

- Sample VMS files from popular games
- Corrupted/malformed files
- Edge cases: empty saves, oversized files
- Real-world messy directory structures

## Security Considerations

### File Safety
- Filename sanitization (prevent path traversal)
- Size validation (prevent memory exhaustion)
- Permission checks (prevent unauthorized writes)

### Data Integrity
- Verify file sizes match expectations
- Validate JSON before writing
- Atomic operations where possible

### Privacy
- No telemetry or data collection
- All processing local
- No network requests (except optional DB fetch)

## Extensibility

### Adding New File Formats

1. Add format to `Scanner.EXTENSIONS`
2. Implement parser in `Parser._parse_xxx()`
3. Update documentation

### Custom Identification Logic

1. Subclass `GameDatabase`
2. Override `identify_game()`
3. Pass custom instance to Organizer

### Output Format Customization

1. Subclass `VMUProWriter`
2. Override `_write_game()` or `_write_channel()`
3. Implement custom directory structure

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Game database contributions

## References

- [VMU Pro SDK Documentation](https://8bitmods.gitbook.io/vmupro-sdk/)
- [Dreamcast VMS Format](http://mc.pp.se/dc/vms/)
- [OpenMenu Database](https://github.com/mrneo240/openMenu_imagedb/)
- [vmu-tools Library](https://github.com/slurmking/vmu-tools)
