import sys
import os
import json
import time

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from services.api_client import RvmApiClient
except ImportError:
    print("Failed to import RvmApiClient")
    sys.exit(1)

# Valid API Key from previous Tinker session
api_key = "K2rzMyHQfGliKJiqeUfA0v59KR0XEttuPLiLDPNEqoLegXvG2I8NiuCDxgIpSNMD"
device_id = "JETSON-ORIN-SN-14239482" 

client = RvmApiClient("http://localhost:8001/api/v1", api_key, device_id, "RVM KU1 (Telemetry Test)")

print("[*] Sending Heartbeat with Bin Capacity (Mock 45%)...")
success = client.heartbeat()

if success:
    print("[+] Heartbeat sent successfully!")
else:
    print("[!] Heartbeat failed.")
