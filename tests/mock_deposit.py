import sys
import os
import json
import time

# Add parent directory to path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.api_client import RvmApiClient

def create_dummy_image(path):
    # Minimal valid JPEG hex string
    # FF D8 FF E0 ...
    minimal_jpg = bytes.fromhex('FFD8FFE000104A46494600010101004800480000FFDB004300030202020202030202020303030304060404040404080606050609080A0A090809090A0C0F0C0A0B0E0B09090D110D0E0F101011100A0C12131210130F101010FFC9000B080001000101011100FFCC000600101005FFDA0008010100003F00D2CF20FFD9')
    with open(path, 'wb') as f:
        f.write(minimal_jpg)
    return path

def main():
    print("=== MOCK DEPOSIT TEST ===")
    
    # Load settings same as main.py
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    with open(creds_path, 'r') as f:
        creds = json.load(f)
        
    client = RvmApiClient(
        base_url=config.get('api_url'), 
        api_key=creds.get('api_key'),
        device_id=config.get('device_id')
    )
    
    print("[*] Initializing Mock Deposit...")
    
    # 1. Create dummy image
    mock_img_path = os.path.join(os.path.dirname(__file__), 'mock_test_bottle.jpg')
    create_dummy_image(mock_img_path)
    print(f"[*] Generated mock image: {mock_img_path}")
    
    # 2. Prepare Metadata
    mock_metadata = {
        "session_id": f"MOCK-SESSION-{int(time.time())}",
        "material": "PLASTIC",
        "weight_g": 15.5,
        "classification_confidence": 0.98,
        "is_accepted": True
    }
    print(f"[*] Mock Payload: {json.dumps(mock_metadata, indent=2)}")
    
    # 3. Send
    print("[*] Sending to Server...")
    success = client.deposit(mock_img_path, mock_metadata)
    
    if success:
        print("[+] MOCK TEST PASSED: Deposit accepted.")
    else:
        print("[-] MOCK TEST FAILED: Deposit rejected.")
        
    # Cleanup
    if os.path.exists(mock_img_path):
        os.remove(mock_img_path)

if __name__ == "__main__":
    main()
