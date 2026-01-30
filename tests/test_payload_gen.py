import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from services.api_client import RvmApiClient
except ImportError:
    # Try adjusting path if running from root
    sys.path.append(os.path.join(os.getcwd(), 'MyRVM-Edge/src'))
    try:
        from services.api_client import RvmApiClient
    except ImportError as e:
        print(f"Error importing RvmApiClient: {e}")
        sys.exit(1)

# Mock client
client = RvmApiClient("http://localhost", "test_key", "DEVICE_123")

print("\n--- SYSTEM INFO ---")
print(json.dumps(client._get_system_info(), indent=2))

print("\n--- HARDWARE INFO ---")
print(json.dumps(client._get_hardware_info(), indent=2))
