import requests
import json
import time
import os
import platform

class RvmApiClient:
    def __init__(self, base_url, api_key, device_id):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.device_id = device_id
        self.session = requests.Session()
        self.session.headers.update({
            'X-RVM-API-KEY': self.api_key,
            'Accept': 'application/json'
        })
        self.machine_info = {}

    def handshake(self, controller_type="Generic"):
        """
        Performs initial handshake to sync identity and config.
        """
        endpoint = f"{self.base_url}/edge/handshake"
        payload = {
            "hardware_id": self.device_id,
            "name": platform.node(),
            "ip_local": self._get_ip(),
            "controller_type": controller_type,
            "health_metrics": {
                "cpu_usage_percent": 0.0, # Placeholder
                "disk_usage_percent": 0.0
            }
        }
        
        try:
            print(f"[*] Handshaking with {endpoint}...")
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                self.machine_info = data['data']
                print(f"[+] Handshake Success! RVM Name: {self.machine_info['identity']['rvm_name']}")
                return True, self.machine_info
            else:
                print(f"[-] Handshake Failed: {data.get('message')}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            print(f"[!] Network Error during Handshake: {str(e)}")
            return False, None

    def deposit(self, image_path, metadata):
        """
        Uploads a deposited item image and metadata.
        """
        endpoint = f"{self.base_url}/edge/deposit"
        
        try:
            if not os.path.exists(image_path):
                print(f"[-] Image file not found: {image_path}")
                return False

            with open(image_path, 'rb') as img_file:
                files = {'image': ('capture.jpg', img_file, 'image/jpeg')}
                data = {'data': json.dumps(metadata), 'status': 'ACCEPTED'}
                
                response = self.session.post(endpoint, files=files, data=data, timeout=15)
                response.raise_for_status()
                
                print(f"[+] Deposit Uploaded: {response.json().get('status')}")
                return True

        except Exception as e:
            print(f"[!] Deposit Error: {str(e)}")
            return False

    def sync_offline(self, transactions):
        """
        Bulk uploads offline transactions.
        """
        endpoint = f"{self.base_url}/edge/sync-offline"
        try:
            payload = {"transactions": transactions}
            response = self.session.post(endpoint, json=payload, timeout=20)
            response.raise_for_status()
            print(f"[+] Offline Sync Success: {response.json().get('synced_count')} items")
            return True
        except Exception as e:
            print(f"[!] Sync Error: {str(e)}")
            return False

    def _get_ip(self):
        # Dummy IP implementation for MVP
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
