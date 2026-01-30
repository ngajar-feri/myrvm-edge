#!/usr/bin/env python3
"""
Test Handshake dengan Mock/Placeholder Data

Menguji fungsi handshake dari api_client.py dengan placeholder
untuk field yang tidak terdeteksi (cameras, sensors, MCU).
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.api_client import RvmApiClient


def print_json(data, title=""):
    """Pretty print JSON data."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    print(json.dumps(data, indent=2, default=str))


def run_mock_handshake_test():
    """
    Test handshake dengan mock data.
    Jika field tidak terdeteksi, akan menggunakan placeholder.
    """
    print("\n" + "="*70)
    print("  MOCK HANDSHAKE TEST - RVM-Edge")
    print("="*70)
    
    # Load credentials if available, otherwise use mock
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    # Try loading real credentials
    try:
        with open(os.path.join(config_dir, 'credentials.json'), 'r') as f:
            creds = json.load(f)
            api_key = creds.get('api_key', 'MOCK_API_KEY_12345')
    except:
        api_key = 'MOCK_API_KEY_12345'
        print("[!] Using MOCK API KEY (credentials.json not found)")
    
    try:
        with open(os.path.join(config_dir, 'settings.json'), 'r') as f:
            settings = json.load(f)
            device_id = settings.get('device_id', 'MOCK_DEVICE_001')
            server_url = settings.get('server_url', 'https://myrvm.penelitian.my.id/api/v1')
    except:
        device_id = 'MOCK_DEVICE_001'
        server_url = 'https://myrvm.penelitian.my.id/api/v1'
        print("[!] Using MOCK settings (settings.json not found)")
    
    # Initialize client
    client = RvmApiClient(
        base_url=server_url,
        api_key=api_key,
        device_id=device_id,
        name="RVM Test Mock"
    )
    
    # Test individual helper methods
    print("\n[1] Testing _get_system_info()...")
    system_info = client._get_system_info()
    print_json(system_info, "System Info")
    
    print("\n[2] Testing _get_hardware_info()...")
    hardware_info = client._get_hardware_info()
    print_json(hardware_info, "Hardware Info")
    
    print("\n[3] Testing _run_diagnostics()...")
    diagnostics = client._run_diagnostics()
    print_json(diagnostics, "Diagnostics")
    
    print("\n[4] Testing _get_health_metrics()...")
    health_metrics = client._get_health_metrics()
    print_json(health_metrics, "Health Metrics")
    
    # Build full payload (without actually sending)
    print("\n[5] Building full handshake payload...")
    full_payload = {
        "hardware_id": device_id,
        "name": client.name,
        "ip_local": client._get_ip(),
        "ip_vpn": client._get_tailscale_ip(),
        "timezone": client._get_timezone(),
        "system": system_info,
        "controller_type": "NVIDIA Jetson",
        "hardware_info": hardware_info,
        "diagnostics": diagnostics,
        "health_metrics": health_metrics,
    }
    print_json(full_payload, "FULL HANDSHAKE PAYLOAD")
    
    # Ask user whether to send to server
    print("\n" + "="*70)
    print("  Payload siap dikirim ke server.")
    print("="*70)
    
    send = input("\nKirim payload ke server? (y/n): ").strip().lower()
    
    if send == 'y':
        print("\n[*] Sending handshake to server...")
        success, response = client.handshake()
        
        if success:
            print("\n[+] HANDSHAKE SUCCESS!")
            print_json(response, "Server Response")
        else:
            print("\n[-] HANDSHAKE FAILED!")
    else:
        print("\n[*] Skipped sending to server.")
    
    print("\n" + "="*70)
    print("  TEST COMPLETED")
    print("="*70 + "\n")


def run_dry_test():
    """
    Dry run - hanya tampilkan payload tanpa kirim.
    """
    print("\n" + "="*70)
    print("  DRY RUN HANDSHAKE TEST - RVM-Edge")
    print("="*70)
    
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    # Load or mock credentials
    try:
        with open(os.path.join(config_dir, 'credentials.json'), 'r') as f:
            creds = json.load(f)
            api_key = creds.get('api_key', 'MOCK_API_KEY')
    except:
        api_key = 'MOCK_API_KEY'
    
    try:
        with open(os.path.join(config_dir, 'settings.json'), 'r') as f:
            settings = json.load(f)
            device_id = settings.get('device_id', 'MOCK_DEVICE')
            server_url = settings.get('server_url', 'https://mock.server/api/v1')
    except:
        device_id = 'MOCK_DEVICE'
        server_url = 'https://mock.server/api/v1'
    
    client = RvmApiClient(server_url, api_key, device_id, "Mock RVM")
    
    payload = {
        "hardware_id": device_id,
        "name": client.name,
        "ip_local": client._get_ip(),
        "ip_vpn": client._get_tailscale_ip(),
        "timezone": client._get_timezone(),
        "system": client._get_system_info(),
        "hardware_info": client._get_hardware_info(),
        "diagnostics": client._run_diagnostics(),
        "health_metrics": client._get_health_metrics(),
    }
    
    print_json(payload, "GENERATED PAYLOAD (DRY RUN)")
    print("\n[*] Tidak dikirim ke server (dry run mode)\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--dry':
        run_dry_test()
    else:
        run_mock_handshake_test()
