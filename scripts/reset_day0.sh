#!/bin/bash

# MyRVM Edge - Day-0 Reset Script
# Use this to return the device to an unprovisioned state.

echo "⚠️  [WARNING] This will RESET the device to Day-0 state!"
echo "    - Deletes secrets.env"
echo "    - Deletes credentials.json"
echo "    - Existing .env (Local Config) will be PRESERVED"
echo ""

read -p "Are you sure you want to proceed? (y/N) " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Aborted."
    exit 1
fi

echo "[*] Stopping myrvm-edge service..."
sudo systemctl stop myrvm-edge.service

echo "[*] Removing configuration..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure we are in the right place
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo "❌ Error: Could not determine PROJECT_DIR (main.py not found in $PROJECT_DIR)"
    exit 1
fi

sudo rm -f "$PROJECT_DIR/config/secrets.env"
sudo rm -f "$PROJECT_DIR/config/credentials.json"
sudo rm -f "$PROJECT_DIR/config/.maintenance_mode"

echo "[*] Restarting service..."
sudo systemctl start myrvm-edge.service

echo "✅ Device reset complete."
echo "   - Setup Wizard should be active on http://<DEVICE_IP>:8080"
echo "   - Check logs with: journalctl -u myrvm-edge.service -f"
