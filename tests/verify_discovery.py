import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.hardware.hardware_manager import HardwareManager

def verify_discovery():
    print("=== [MOCK] MyRVM Edge Discovery Verification ===")
    
    # Initialize Manager
    hw = HardwareManager()
    
    # Run Probe
    print("[*] Running Hardware Discovery Probe...")
    report = hw.get_discovery_report()
    
    print("\n[MOCK] --- Discovery Report ---")
    print(json.dumps(report, indent=2))
    
    # Basic Checks
    if len(report['reality']['serial_ports']) > 0:
        print("[MOCK] [x] Serial Port Detection: OK")
    else:
        print("[MOCK] [!] No Serial Ports detected.")
        
    print(f"[MOCK] [x] Configuration Audit: {report['configured_count']} drivers mapped.")
    print("=== [MOCK] VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    verify_discovery()
