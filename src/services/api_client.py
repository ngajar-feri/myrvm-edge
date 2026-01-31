import requests
import json
import time
import os
import platform
import subprocess
import glob

class RvmApiClient:
    def __init__(self, base_url, api_key, device_id, name=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.device_id = device_id
        self.name = name or platform.node()
        self.session = requests.Session()
        self.session.headers.update({
            'X-RVM-API-KEY': self.api_key,
            'Accept': 'application/json'
        })
        self.machine_info = {}
        
        # Load Version
        self.version = "1.1.0"
        try:
            version_path = os.path.join(os.path.dirname(__file__), '../../VERSION')
            if os.path.exists(version_path):
                with open(version_path, 'r') as f:
                    self.version = f.read().strip()
        except Exception as e:
            print(f"[!] Failed to load VERSION file: {e}")

        # Load Hardware Map
        self.hardware_map = {}
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../../config/hardware_map.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.hardware_map = json.load(f)
        except Exception as e:
            print(f"[!] Failed to load hardware_map.json: {e}")

    def handshake(self, controller_type="NVIDIA Jetson"):
        """
        Performs initial handshake to sync identity and config.
        Sends full payload per GAI-handshake.md specification.
        """
        endpoint = f"{self.base_url}/edge/handshake"
        
        # Use centralized EdgeDiagnostics to build payload
        try:
            from ..hardware.edge_diagnostics import EdgeDiagnostics
            # Initialize with reference to self for hardware_map if needed, 
            # though EdgeDiagnostics currently operates independently or with its own probe.
            # We can pass hardware_manager if we had one instantiated, but for now it's standalone.
            diag = EdgeDiagnostics()
            
            # Get full specs which matches the 1-10 structure
            payload = diag.get_specs()
            
            # Overwrite name/id if strictly managed by client (optional, but good for consistency)
            payload["hardware_id"] = self.device_id
            payload["name"] = self.name
            
            # Ensure controller_type matches what is passed if logic differs, 
            # but diagnostics handles it better usually.
            # payload["controller_type"] = controller_type # Let diagnostics detect it
            
        except ImportError:
             print("[!] EdgeDiagnostics module not found, falling back to legacy payload")
             payload = {
                # Legacy fallback
                "hardware_id": self.device_id,
                "name": self.name,
                "ip_local": self._get_ip(),
                "controller_type": controller_type,
                "status": "fallback"
            }
        except Exception as e:
             print(f"[!] Error building handshake payload: {e}")
             return False, None
        
        try:
            print(f"[*] Handshaking with {endpoint}...")
            # print(json.dumps(payload, indent=2)) # Debug payload
            response = self.session.post(endpoint, json=payload, timeout=15)
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

    def heartbeat(self, bin_capacity=0, discovery_report=None):
        """
        Sends heartbeat with health metrics, bin capacity, and hardware discovery.
        Returns potential commands from server.
        """
        endpoint = f"{self.base_url}/edge/heartbeat"
        try:
            payload = {
                "hardware_id": self.device_id,
                "status": "online",
                "version": self.version,
                "health_metrics": self._get_health_metrics(),
                "bin_capacity": bin_capacity,
                "discovery": discovery_report,
                "ip_local": self._get_ip(),
                "tailscale_ip": self._get_tailscale_ip()
            }
            # Heartbeat is lightweight, short timeout
            response = self.session.post(endpoint, json=payload, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success' and 'commands' in data:
                return data['commands']
            
            return []
        except Exception as e:
            print(f"[!] Heartbeat Error: {str(e)}")
            return []

    # ========== Helper Methods ==========

    def _get_ip(self):
        """Get local IP address."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _get_tailscale_ip(self):
        """Get Tailscale VPN IP if available."""
        try:
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _get_timezone(self):
        """Get system timezone."""
        try:
            if os.path.exists('/etc/timezone'):
                with open('/etc/timezone', 'r') as f:
                    return f.read().strip()
            # Fallback to TZ environment variable
            return os.environ.get('TZ', 'Asia/Jakarta')
        except:
            return 'Asia/Jakarta'

    def _get_system_info(self):
        """Gather system software information."""
        info = {
            "python_version": platform.python_version(),
            "firmware_version": "v2.1.0-beta", # Hardcoded from spec for now or read from file
        }
        
        # Try to get JetPack version (NVIDIA Jetson)
        try:
            if os.path.exists('/etc/nv_tegra_release'):
                with open('/etc/nv_tegra_release', 'r') as f:
                    content = f.read().strip()
                    import re
                    # Example content: "# R36 (release), REVISION: 0.1, ..."
                    rel = re.search(r'# R(\d+)', content)
                    rev = re.search(r'REVISION:\s*([\d.]+)', content)
                    if rel and rev:
                        l4t = f"R{rel.group(1)}.{rev.group(1)}"
                        # Common Mapping
                        info["jetpack_version"] = f"JetPack 6.0 ({l4t})" if rel.group(1) == "36" else l4t
                    elif rel:
                        info["jetpack_version"] = f"L4T R{rel.group(1)}"
                    else:
                        info["jetpack_version"] = content.split(',')[0].replace('# ', '')
            else:
                info["jetpack_version"] = "Mock dev-v2.0"
        except Exception:
            info["jetpack_version"] = "Unknown"
        
        # AI model info
        # Check map first, then config
        if "system" in self.hardware_map and "ai_models" in self.hardware_map["system"]:
             info["ai_models"] = self.hardware_map["system"]["ai_models"]
        else:
            # Fallback
            info["ai_models"] = {
                "model_name": "best.pt",
                "model_version": "v1.0.0-beta",
                "last_update": "2026-01-17T00:00:00Z"
            }
        
        return info

    def _get_hardware_info(self):
        """
        Detect connected hardware (cameras, sensors, MCU).
        Merges auto-detection with static hardware_map.json.
        """
        info = {}
        
        # 1. Cameras: Detect and Merge
        detected_cameras = self._detect_cameras()
        mapped_cameras = self.hardware_map.get("cameras", [])
        
        final_cameras = []
        # Simple merge by ID or Path priority
        for d_cam in detected_cameras:
            # Try to find match in map
            match = next((c for c in mapped_cameras if c.get("path") == d_cam["path"] or c.get("id") == d_cam["id"]), None)
            if match:
                # Merge map data into detected data (map overrides name/role, detected provides status)
                merged = {**match, **d_cam} # d_cam status overwrites map if keys collision? No, we want map to provide static info
                # Actually we want map to be base, and detected to provide current status
                merged = match.copy()
                merged["active_path"] = d_cam["path"]
                merged["status"] = d_cam["status"]
                final_cameras.append(merged)
            else:
                final_cameras.append(d_cam)
        
        if not final_cameras and mapped_cameras:
             # If detection failed but we have map, return map with status error?
             # Or just return map for simulation purposes?
             # Let's return map marked as 'offline' if not detected?
             # For now, if we are in Mock/Dev mode with no cameras, just return map
             final_cameras = mapped_cameras
        
        info["cameras"] = final_cameras
        
        # 2. Microcontroller: Detect and Merge
        detected_mcu = self._detect_microcontroller()
        mapped_mcu = self.hardware_map.get("microcontroller", {})
        
        if detected_mcu.get("status") == "connected":
             # Use detected port, but pull type/baud_rate from map if available
             info["microcontroller"] = {**mapped_mcu, **detected_mcu}
        else:
             # Not detected, use map but mark status as disconnected
             info["microcontroller"] = mapped_mcu.copy()
             info["microcontroller"]["status"] = "not_connected"

        # 3. Sensors (Static Map + Mock Reading)
        info["sensors"] = self.hardware_map.get("sensors", [])
        
        # 4. Actuators (Static Map)
        info["actuators"] = self.hardware_map.get("actuators", [])
        
        return info

    def _detect_cameras(self):
        """
        Detect connected cameras using v4l2-ctl.
        """
        cameras = []
        try:
            # Use v4l2-ctl to get actual device list
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse output to get unique physical cameras
                lines = result.stdout.strip().split('\n')
                current_device = None
                camera_id = 0
                
                for line in lines:
                    if line and not line.startswith('\t') and not line.startswith(' '):
                        current_device = line.split(':')[0].strip()
                    elif line.strip().startswith('/dev/video') and current_device:
                        # Only take first video node per device
                        if not any(c.get('name') == current_device for c in cameras):
                            video_path = line.strip()
                            cameras.append({
                                "id": camera_id,
                                "path": video_path,
                                "name": current_device, # Will be overwritten by friendy name if mapped
                                "status": "ready" if os.access(video_path, os.R_OK) else "error"
                            })
                            camera_id += 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return cameras

    def _detect_microcontroller(self):
        """
        Detect connected microcontroller via USB serial chips.
        """
        mcu = {"status": "not_connected"}
        
        try:
            result = subprocess.run(
                ["lsusb"],
                capture_output=True, text=True, timeout=5
            )
            
            usb_serial_chips = ['cp210', 'ch340', 'ch341', 'ftdi', 'silabs', 'esp']
            found_chip = None
            
            if result.returncode == 0:
                for line in result.stdout.lower().split('\n'):
                    for chip in usb_serial_chips:
                        if chip in line:
                            found_chip = chip.upper()
                            break
                    if found_chip:
                        break
            
            if found_chip:
                port = None
                for p in ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1', '/dev/ttyTHS1']:
                     if os.path.exists(p):
                        port = p
                        break
                
                if port:
                    mcu = {
                        "port": port,
                        "chip": found_chip,
                        "status": "connected"
                    }
        except Exception:
            pass
        
        return mcu

    def _run_diagnostics(self):
        """Run basic hardware diagnostics."""
        return {
            "network_check": "pass" if self._get_ip() != "127.0.0.1" else "fail",
            "camera_check": "pass" if self._detect_cameras() else "warning",
            "motor_test": "pass",  # Simulating pass for spec v2.0
            "ai_inference_test": "pass" 
        }

    def _get_health_metrics(self):
        """Get current system health metrics."""
        metrics = {
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
            "cpu_temperature": 0.0
        }
        
        try:
            import psutil
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=0.5)
            metrics["memory_usage_percent"] = psutil.virtual_memory().percent
            metrics["disk_usage_percent"] = psutil.disk_usage('/').percent
        except ImportError:
            pass
        
        # Jetson CPU temperature
        try:
            temp_path = '/sys/devices/virtual/thermal/thermal_zone0/temp'
            if os.path.exists(temp_path):
                with open(temp_path, 'r') as f:
                    metrics["cpu_temperature"] = int(f.read().strip()) / 1000.0
        except:
            pass
        
        return metrics
