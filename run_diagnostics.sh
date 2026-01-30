#!/bin/bash
# Hardware Diagnostics Runner
# Sets up path and runs the diagnostics module

# Ensure we are in the project root
cd "$(dirname "$0")"

# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Starting Hardware Diagnostics..."
python3 -m src.hardware.edge_diagnostics
