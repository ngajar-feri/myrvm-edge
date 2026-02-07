#!/bin/bash

# MyRVM Edge Service Setup Script
# Usage: sudo ./setup_service.sh

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

WORKING_DIR=$(pwd)
if [[ $WORKING_DIR == */scripts ]]; then
    WORKING_DIR=$(dirname "$WORKING_DIR")
fi

# Detect User
REAL_USER=${SUDO_USER:-$USER}
echo "[*] Detected User: $REAL_USER"
echo "[*] Working Directory: $WORKING_DIR"

# Virtual Environment Setup
echo "[*] Setting up Virtual Environment (venv)..."
if [ ! -d "$WORKING_DIR/venv" ]; then
    python3 -m venv "$WORKING_DIR/venv"
    chown -R $REAL_USER:$REAL_USER "$WORKING_DIR/venv"
fi

# Install Dependencies
echo "[*] Installing dependencies in venv..."
sudo -u $REAL_USER "$WORKING_DIR/venv/bin/pip" install --upgrade pip
sudo -u $REAL_USER "$WORKING_DIR/venv/bin/pip" install -r "$WORKING_DIR/requirements.txt"

# Stop existing manual processes
echo "[*] Stopping existing manual python processes..."
pkill -f "python.*main.py" || true

# Prepare Service Files
echo "[*] Preparing systemd service files..."
sed "s|{{USER}}|$REAL_USER|g; s|{{WORKING_DIR}}|$WORKING_DIR|g" "$WORKING_DIR/scripts/myrvm-edge.service" > /etc/systemd/system/myrvm-edge.service
sed "s|{{USER}}|$REAL_USER|g; s|{{WORKING_DIR}}|$WORKING_DIR|g" "$WORKING_DIR/scripts/myrvm-updater.service" > /etc/systemd/system/myrvm-updater.service
cp "$WORKING_DIR/scripts/myrvm-updater.timer" /etc/systemd/system/

# Reload and Enable
echo "[*] Enabling services..."
systemctl daemon-reload
systemctl enable myrvm-edge.service
systemctl enable myrvm-updater.timer

# Start
echo "[*] Starting services..."
systemctl restart myrvm-edge.service
systemctl restart myrvm-updater.timer

echo "[+] Setup complete!"
systemctl status myrvm-edge.service --no-pager
