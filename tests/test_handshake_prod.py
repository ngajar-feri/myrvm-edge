#!/usr/bin/env python3
"""
Test Handshake dengan Data Produksi (RVM-202601-006)

Menguji fungsi handshake dari api_client.py dengan menggunakan
kredensial asli yang dihasilkan oleh server.
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

def run_production_handshake_test():
    """
    Test handshake dengan data produksi.
    """
    print("\n" + "="*70)
    print("  PRODUCTION HANDSHAKE TEST - RVM-Edge")
    print("="*70)
    
    # Production Credentials
    api_key = "Mpy2X292Yj0ByeY22HrvhS3lHLHEyJ5dLShUPKWdrDHM753oWQs5wwBzIu1s0VIk"
    device_id = "RVM-202601-006"
    name = "RVM KU1"
    server_url = "https://myrvm.penelitian.my.id/api/v1"
    
    print(f"[*] Target: {server_url}")
    print(f"[*] Device ID: {device_id}")
    print(f"[*] Name: {name}")
    
    # Initialize client
    client = RvmApiClient(
        base_url=server_url,
        api_key=api_key,
        device_id=device_id,
        name=name
    )
    
    # Perform handshake
    print("\n[*] Initializing handshake with server...")
    success, response = client.handshake()
    
    if success:
        print("\n[+] HANDSHAKE SUCCESS!")
        print_json(response, "Server Response")
    else:
        print("\n[-] HANDSHAKE FAILED!")
        if hasattr(client, 'last_response') and client.last_response:
             print(f"[-] Status Code: {client.last_response.status_code}")
             print(f"[-] Body: {client.last_response.text}")
    
    print("\n" + "="*70)
    print("  TEST COMPLETED")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_production_handshake_test()
