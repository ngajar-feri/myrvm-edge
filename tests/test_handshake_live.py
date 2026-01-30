import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.path.join(os.getcwd(), 'MyRVM-Edge/src'))

try:
    from services.api_client import RvmApiClient
except ImportError:
    print("Failed to import RvmApiClient")
    sys.exit(1)

# API Key - Using a valid one if known, or one that works for the device. 
# Assuming unconfigured device might need valid key? 
# In V2 logic, maybe it just sends hardware_id.
# Let's try with a dummy key first or see if I can find a valid one in DB.
# For now, I'll use "test_api_key" and see if middleware blocks it.
# Actually I modified Middleware to accept plaintext keys.
api_key = "K2rzMyHQfGliKJiqeUfA0v59KR0XEttuPLiLDPNEqoLegXvG2I8NiuCDxgIpSNMD"

# Hardware ID from User Spec
device_id = "JETSON-ORIN-SN-14239482" 

client = RvmApiClient("http://localhost:8001/api/v1", api_key, device_id, "RVM KU1 (Spec V2)")
success, info = client.handshake()

if success:
    print("\nSUCCESS: Handshake completed.")
    print("Server response data:")
    print(json.dumps(info, indent=2))
else:
    print("\nFAILED: Handshake failed.")
