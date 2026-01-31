#!/bin/bash

# MyRVM Edge Service Manager
# Deskripsi: Menu interaktif untuk ON / OFF / RESTART service di Raspberry Pi

# Warna
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SERVICES=("myrvm-edge" "myrvm-updater")

show_status() {
    echo -e "${CYAN}=== Status Service ===${NC}"
    for service in "${SERVICES[@]}"; do
        status=$(systemctl is-active $service 2>/dev/null || echo "not-found")
        if [ "$status" == "active" ]; then
            echo -e "$service: ${GREEN}RUNNING${NC}"
        elif [ "$status" == "not-found" ]; then
             echo -e "$service: ${RED}NOT INSTALLED${NC}"
        else
            echo -e "$service: ${RED}STOPPED ($status)${NC}"
        fi
    done
}

show_menu() {
    clear
    echo -e "${CYAN}=======================================${NC}"
    echo -e "${CYAN}    MyRVM EDGE SERVICE MANAGER         ${NC}"
    echo -e "${CYAN}=======================================${NC}"
    show_status
    echo -e "${CYAN}---------------------------------------${NC}"
    echo -e "1) ${GREEN}TURN ON (Enable + Start)${NC}"
    echo -e "2) ${RED}TURN OFF (Stop + Disable)${NC}"
    echo -e "3) ${YELLOW}RESTART Services${NC}"
    echo -e "4) ${BLUE}Check Status${NC}"
    echo -e "q) Exit"
    echo -e "${CYAN}=======================================${NC}"
}

execute_action() {
    case "$1" in
        1|on)
            echo -e "${YELLOW}Menjalankan service...${NC}"
            sudo systemctl enable "${SERVICES[@]}"
            sudo systemctl start "${SERVICES[@]}"
            sleep 2
            ;;
        2|off)
            echo -e "${YELLOW}Menghentikan service...${NC}"
            sudo systemctl stop "${SERVICES[@]}"
            sudo systemctl disable "${SERVICES[@]}"
            sleep 1
            ;;
        3|restart)
            echo -e "${YELLOW}Me-restart service...${NC}"
            sudo systemctl restart "${SERVICES[@]}"
            sleep 2
            ;;
        4|status)
            echo -e ""
            show_status
            echo -e "\nTekan [Enter] untuk melanjutkan..."
            read -r
            ;;
        q|Q)
            echo -e "${GREEN}Sampai jumpa!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opsi tidak valid!${NC}"
            sleep 1
            ;;
    esac
}

# Jika ada argumen (misal: ./manage_service.sh on), jalankan langsung tanpa menu
if [ $# -gt 0 ]; then
    execute_action "$1"
    exit 0
fi

# Jika tidak ada argumen, tampilkan menu interaktif
while true; do
    show_menu
    read -p "Pilih opsi [1-4 atau q]: " opt
    execute_action "$opt"
done
