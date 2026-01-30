import sys
import time
import json
import os
import subprocess
from pathlib import Path
def load_env_file(path):
    """Simple replacement for load_dotenv to avoid external dependency."""
    if not os.path.exists(path): return
    with open(path, 'r') as f:
        for line in f:
            if '=' in line:
                key, val = line.strip().split('=', 1)
                os.environ[key] = val

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from src.services.api_client import RvmApiClient
from src.hardware.hardware_manager import HardwareManager

# Constants
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.env"

def get_device_info():
    """Extracts physical hardware serial and model name (Jetson/Pi)."""
    # 1. Check for Jetson
    if os.path.exists('/proc/device-tree/model'):
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip('\x00').strip()
            
            serial = "unknown_jetson"
            if os.path.exists('/proc/device-tree/serial-number'):
                with open('/proc/device-tree/serial-number', 'r') as f:
                    serial = f.read().strip('\x00').strip()
            return serial, model
        except Exception as e:
            print(f"[!] Error reading Jetson info: {e}")

    # 2. Check for Raspberry Pi
    if os.path.exists('/proc/cpuinfo'):
        try:
            is_pi = False
            serial = "unknown_pi"
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                if 'Raspberry Pi' in content or 'BCM2835' in content or 'BCM2711' in content:
                    is_pi = True
                
                # Extract serial if available
                import re
                match = re.search(r'^Serial\s*:\s*([0-9a-fA-F]+)', content, re.MULTILINE)
                if match:
                    serial = match.group(1)
            
            if is_pi:
                return serial, "Raspberry Pi"
        except Exception as e:
            print(f"[!] Error reading Pi info: {e}")

    return "generic_dev", "Generic Linux Device"

def run_setup_wizard():
    """Launches the FastAPI Setup Wizard in a blocking sub-process."""
    print("=== STARTING SETUP WIZARD (Day-0) ===")
    print("[*] No configuration found.")
    print("[*] Launching Web Interface at http://0.0.0.0:8080")
    print("[*] Please upload rvm-credentials.json to provision.")
    
    try:
        # Run uvicorn as a subprocess
        subprocess.run(
            ["uvicorn", "src.setup_wizard.app:app", "--host", "0.0.0.0", "--port", "8080"], 
            check=True
        )
    except KeyboardInterrupt:
        print("\n[!] Wizard stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Wizard crashed: {e}")
        sys.exit(1)

def main():
    print("=== MyRVM Edge Client v2.0 (Day-0 Ready) ===")
    
    # 1. Check for Provisioning
    if not SECRETS_PATH.exists():
        run_setup_wizard()
        # If wizard finishes (returns), it means we might want to restart?
        # Typically uvicorn runs forever until killed.
        # But if we implement a restart mechanism in app.py, this script might exit.
        print("[*] Wizard exited. Checking for config...")
        if not SECRETS_PATH.exists():
            print("[!] Still not provisioned. Exiting.")
            sys.exit(1)
        print("[*] Provisioned! Proceeding to boot...")

    # 2. Load Credentials
    load_env_file(SECRETS_PATH)
    api_key = os.getenv("RVM_API_KEY")
    serial_number = os.getenv("RVM_SERIAL_NUMBER")
    
    if not api_key:
        print("[!] Invalid secrets.env. Missing API Key.")
        sys.exit(1)

    # 3. Hardware Info
    hw_serial, model = get_device_info()
    
    # Override HW Serial if provided in JSON (usually we want Physical, but maybe Logic ID?)
    # Spec says: hardware_id: "RVM-202601-006" from json.
    # But physical ID is useful for asset tracking. 
    # Let's use the one from secrets as the "Logical ID" for Handshake.
    
    print(f"[*] Logic ID: {serial_number}")
    print(f"[*] Physical ID: {hw_serial}")
    print(f"[*] Controller: {model}")
    
    # 4. Initialize API Client
    # Default URL from spec
    server_url = "https://myrvm.penelitian.my.id/api/v1" 
    
    client = RvmApiClient(
        base_url=server_url, 
        api_key=api_key,
        device_id=serial_number # Using Logical Serial from JSON
    )
    
    # 5. Handshake Loop
    print("[*] Initiating Handshake...")
    handshake_success = False
    config = {}
    
    while not handshake_success:
        handshake_success, config = client.handshake(controller_type=model)
        if not handshake_success:
            print("[!] Handshake failed. Retrying in 5 seconds...")
            time.sleep(5)
            
    print(f"[*] Handshake Success! Kiosk URL: {config.get('kiosk', {}).get('url')}")
            
    # 6. Initialize Hardware
    print("[*] Initializing Hardware Drivers...")
    hw = HardwareManager()
    hw.initialize_all()
    
    # 7. Main Loop
    print("[*] Starting Local WebSocket Bridge provided by RVM-Edge...")
    local_ws_process = subprocess.Popen(
        [sys.executable, "src/network/ws_local.py"],
        cwd=BASE_DIR
    )

    print("[*] Entering Main Loop...")
    try:
        while True:
            time.sleep(10)
            
            # Read real bin capacity if driver exists
            bin_driver = hw.get_driver('bin_ultrasonic')
            bin_level = 0
            if bin_driver:
                distance = bin_driver.read()
                if distance:
                    # Logic: Smaller distance = fuller bin.
                    # Assume 50cm is empty, 5cm is full.
                    bin_level = max(0, min(100, int((50 - distance) / 45 * 100)))
                    print(f"[.] Bin Distance: {distance} cm -> {bin_level}% full")
            
            # Dynamic Hardware Probe
            discovery = hw.get_discovery_report()
            
            print("[.] Heartbeat with Discovery...")
            commands = client.heartbeat(bin_capacity=bin_level, discovery_report=discovery)
            if commands:
                handle_commands(commands)
            
            if "--once" in sys.argv:
                print("[*] --once flag detected. Exiting loop.")
                break
            
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
        hw.cleanup()
        local_ws_process.terminate()
        local_ws_process.wait()

if __name__ == "__main__":
    main()
