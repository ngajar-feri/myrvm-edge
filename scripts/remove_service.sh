#!/bin/bash

# MyRVM Edge Service Removal Script
# Usage: sudo ./remove_service.sh

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

echo "[*] Stopping and disabling services..."
systemctl stop myrvm-edge.service || true
systemctl disable myrvm-edge.service || true
systemctl stop myrvm-updater.timer || true
systemctl disable myrvm-updater.timer || true

echo "[*] Removing service files..."
rm -f /etc/systemd/system/myrvm-edge.service
rm -f /etc/systemd/system/myrvm-updater.service
rm -f /etc/systemd/system/myrvm-updater.timer

systemctl daemon-reload
echo "[+] Services removed successfully."
