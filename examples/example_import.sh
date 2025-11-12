#!/bin/bash
# Example: Import VMU saves to VMU Pro structure

# This script demonstrates common import scenarios

echo "VMU Pro SD Save Importer - Examples"
echo "===================================="
echo

# Example 1: Basic import with dry-run
echo "Example 1: Preview import (dry-run)"
echo "-----------------------------------"
python ../vmupro_importer.py \
  --input ./sample_saves \
  --output ./output_preview \
  --dry-run
echo

# Example 2: Actual import with verbose logging
echo "Example 2: Import with verbose logging"
echo "--------------------------------------"
python ../vmupro_importer.py \
  --input ./sample_saves \
  --output ./output_actual \
  --verbose
echo

# Example 3: Import with custom settings
echo "Example 3: Import with custom settings"
echo "--------------------------------------"
python ../vmupro_importer.py \
  --input ./sample_saves \
  --output ./output_custom \
  --max-channels 4 \
  --verbose
echo

# Example 4: Import with custom game database
echo "Example 4: Import with custom database"
echo "--------------------------------------"
python ../vmupro_importer.py \
  --input ./sample_saves \
  --output ./output_custom_db \
  --database ./custom_games.json
echo

echo "Examples completed!"
echo "Check the output directories to see results"
