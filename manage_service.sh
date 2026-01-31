#!/bin/bash

# MyRVM Edge Service Manager
# Digunakan untuk ON / OFF / RESTART service di Raspberry Pi

NC='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'

SERVICES=("myrvm-edge" "myrvm-updater")

show_status() {
    echo -e "${CYAN}=== Status Service ===${NC}"
    for service in "${SERVICES[@]}"; do
        status=$(systemctl is-active $service)
        if [ "$status" == "active" ]; then
            echo -e "$service: ${GREEN}RUNNING${NC}"
        else
            echo -e "$service: ${RED}STOPPED ($status)$NC}"
        fi
    done
}

case "$1" in
    on)
        echo -e "${YELLOW}Menjalankan service...${NC}"
        sudo systemctl enable "${SERVICES[@]}"
        sudo systemctl start "${SERVICES[@]}"
        sleep 2
        show_status
        ;;
    off)
        echo -e "${YELLOW}Menghentikan service...${NC}"
        sudo systemctl stop "${SERVICES[@]}"
        sudo systemctl disable "${SERVICES[@]}"
        sleep 1
        show_status
        ;;
    restart)
        echo -e "${YELLOW}Me-restart service...${NC}"
        sudo systemctl restart "${SERVICES[@]}"
        sleep 2
        show_status
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "Usage: $0 {on|off|restart|status}"
        exit 1
        ;;
esac
