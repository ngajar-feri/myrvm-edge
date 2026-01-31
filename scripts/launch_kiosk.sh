#!/bin/bash

# MyRVM Kiosk Launcher
# Version: 1.1.0
# Description: Launches browser in kiosk mode for MyRVM interface.

URL=$1
BROWSER_PREF=${2:-"auto"} # auto, firefox, chromium

if [ -z "$URL" ]; then
    echo "Usage: $0 <URL> [auto|firefox|chromium]"
    exit 1
fi

# Display Settings (Crucial for execution via SSH or Systemd)
export DISPLAY=${DISPLAY:-:0}
# XAUTHORITY should be set to the user who is logged into the desktop
# On Raspberry Pi OS, this is usually 'pi' or the main user
CURRENT_USER=$(whoami)
export XAUTHORITY=${XAUTHORITY:-/home/$CURRENT_USER/.Xauthority}

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

launch_firefox() {
    if command -v firefox > /dev/null; then
        log "[*] Launching Firefox Kiosk: $URL"
        # Firefox kiosk flags
        firefox --kiosk "$URL" &
        return 0
    fi
    return 1
}

launch_chromium() {
    # Check for various chromium binary names
    CHROME_BIN=""
    if command -v chromium-browser > /dev/null; then
        CHROME_BIN="chromium-browser"
    elif command -v chromium > /dev/null; then
        CHROME_BIN="chromium"
    elif command -v google-chrome > /dev/null; then
        CHROME_BIN="google-chrome"
    fi

    if [ -n "$CHROME_BIN" ]; then
        log "[*] Launching Chromium Kiosk: $URL"
        FLAGS="--kiosk \
               --incognito \
               --no-first-run \
               --disable-infobars \
               --disable-session-crashed-bubble \
               --disable-features=TranslateUI \
               --noerrdialogs \
               --disable-component-update \
               --check-for-update-interval=31536000 \
               --overscroll-history-navigation=0"
        $CHROME_BIN $FLAGS "$URL" &
        return 0
    fi
    return 1
}

# Optional: Hide mouse cursor
if command -v unclutter > /dev/null; then
    unclutter -idle 0.1 -root &
fi

case $BROWSER_PREF in
    firefox)
        launch_firefox || launch_chromium
        ;;
    chromium)
        launch_chromium || launch_firefox
        ;;
    *)
        # Default: try firefox first since user mentioned it works better on Raspi
        launch_firefox || launch_chromium || log "[!] No supported browser found."
        ;;
esac
