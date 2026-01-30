import time
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Standard Mock Check (following mock-data-consistency.md)
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Use mocks if hardware library is not present
    mock_gpio = MagicMock()
    sys.modules["RPi"] = MagicMock()
    sys.modules["RPi.GPIO"] = mock_gpio
    sys.modules["Jetson"] = MagicMock()
    sys.modules["Jetson.GPIO"] = mock_gpio
    print("[MOCK] GPIO hardware not detected. Running in SIMULATION mode.")
else:
    print("[HARDWARE] GPIO detected. Running in PHYSICAL mode.")

from src.hardware.hardware_manager import HardwareManager

def mock_run_stress_test(duration_minutes=10, interval_seconds=2):
    print(f"=== Starting Stress Test ({duration_minutes}m, every {interval_seconds}s) ===")
    
    mgr = HardwareManager()
    mgr.initialize_all()
    
    bin_driver = mgr.get_driver('bin_ultrasonic')
    iterations = int((duration_minutes * 60) / interval_seconds)
    
    start_time = time.time()
    
    try:
        for i in range(iterations):
            current_time = time.ctime()
            if bin_driver:
                val = bin_driver.read()
                # Following mock-data-consistency.md: all output includes clear indicator
                p_type = "[MOCK]" if "MagicMock" in str(type(bin_driver)) else "[REAL]"
                print(f"{p_type} [{current_time}] Iteration {i+1}/{iterations}: Bin Distance: {val} cm")
            
            # Simple heartbeat log
            if (i+1) % 30 == 0:
                print(f"[*] Progressive Status: {int((i+1)/iterations*100)}% complete")
                
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n[!] Stress test interrupted by user.")
    finally:
        mgr.cleanup()
        end_time = time.time()
        print(f"=== Stress Test Finished. Total Duration: {round(end_time - start_time, 2)}s ===")

if __name__ == "__main__":
    # If run with --once, it only runs one iteration for validation
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        mock_run_stress_test(duration_minutes=0.04, interval_seconds=1) # ~2 seconds
    else:
        mock_run_stress_test()
