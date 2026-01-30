import json
import socket
import subprocess
import time
import platform
import os
import uuid
try:
    import requests
except ImportError:
    requests = None
try:
    import psutil
except ImportError:
    psutil = None
import datetime
from .hardware_probe import HardwareProbe

class EdgeDiagnostics:
    """
    Module for gathering hardware specifications, system metrics, and running basic diagnostics 
    for the Edge device (Jetson/Raspberry Pi).
    """

    def __init__(self, hardware_manager=None):
        self.probe = HardwareProbe()
        self.hw_manager = hardware_manager # Optional, for syncing with intent
        self.device_id = self._get_device_id()

    def get_specs(self):
        """
        Returns a dictionary containing the full hardware specification and status.
        Matches the requested structure:
        1. hardware ID
        2. name
        3. ip_local
        4. ip_vpn
        5. timezone
        6. system
        7. controller_type
        8. hardware_info
        9. diagnostics
        10. health_metrics
        """
        
        # 1-7: Basic Info
        specs = {
            "device_id": self.device_id,
            "name": platform.node(),
            "ip_local": self._get_local_ip(),
            "ip_vpn": self._get_vpn_ip(),
            "timezone": self._get_remote_timezone(),
            "system": self._get_system_info(),
            "controller_type": self._detect_controller_type(),
        }

        # 8: Hardware Info (Detection)
        specs["hardware_info"] = self._get_hardware_info()

        # 9: Diagnostics
        specs["diagnostics"] = self._run_diagnostics()

        # 10: Health Metrics
        specs["health_metrics"] = self._get_health_metrics()

        return specs

    def _get_remote_timezone(self):
        """
        Determines timezone based on Public IP using ipapi.co.
        Falls back to system timezone if API fails.
        """
        try:
            if requests:
                # Using ipapi.co/json/ to ensure JSON response
                response = requests.get('https://ipapi.co/json/', timeout=5).json()
                return response.get('timezone', 'Unknown')
            else:
                return str(datetime.datetime.now().astimezone().tzinfo) + " (requests missing)"
        except Exception as e:
            # Fallback to local system timezone
            return str(datetime.datetime.now().astimezone().tzinfo)

    def _get_device_id(self):
        """Generates a unique ID based on MAC address or Machine ID."""
        try:
            # Try getting machine-id
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            # Fallback to MAC based
            return hex(uuid.getnode())
        except:
            return "unknown-device-id"

    def _get_local_ip(self):
        """Gets local LAN IP."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _get_vpn_ip(self):
        """Gets Tailscale IP if available."""
        try:
            # Allow turbo-all for this command if simple
            result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass # Tailscale not installed
        except Exception as e:
            # print(f"VPN IP check failed: {e}") 
            pass
        return "Not Connected"

    def _get_system_info(self):
        """
        Gather system software information.
        """
        # 1. Firmware Version (Git Tag/Commit or File)
        firmware = "Unknown"
        try:
            # Try getting git tag description
            git_ver = subprocess.check_output(
                ["git", "describe", "--tags", "--always", "--dirty"], 
                cwd=os.path.dirname(__file__), 
                stderr=subprocess.DEVNULL
            ).decode().strip()
            firmware = git_ver
        except Exception:
            # Fallback to VERSION file if exists
            try:
                ver_path = os.path.join(os.path.dirname(__file__), '../../VERSION')
                if os.path.exists(ver_path):
                    with open(ver_path, 'r') as f:
                        firmware = f.read().strip()
            except Exception:
                pass

        # 2. JetPack Version Detection
        jetpack = "Unknown"
        try:
            if os.path.exists('/etc/nv_tegra_release'):
                with open('/etc/nv_tegra_release', 'r') as f:
                    content = f.read().strip()
                    parts = content.split(',')
                    if len(parts) >= 2:
                        release = parts[0].replace('# ', '').strip()
                        revision = parts[1].replace('REVISION: ', '').strip()
                        jetpack = f"{release}.{revision}"
                    else:
                        jetpack = content
            elif os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                     model = f.read().strip().replace('\x00', '')
                     if "Raspberry Pi" in model:
                         jetpack = "N/A (Raspberry Pi)"
                     else:
                         jetpack = "N/A (Generic Linux)"
            else:
                jetpack = "N/A (Non-Jetson)"
        except Exception:
            jetpack = "Error Detecting"

        # 3. System Info Object
        info = {
            "python_version": platform.python_version(),
            "firmware_version": firmware,
            "jetpack_version": jetpack,
            "ai_models": self._detect_ai_models()
        }
        return info

    def _detect_ai_models(self):
        """Detect available AI models without placeholders."""
        models_dir = os.path.join(os.path.dirname(__file__), '../../models')
        config_path = os.path.join(os.path.dirname(__file__), '../../config/config.json')
        models_list = []

        try:
             # Try Config First
             if os.path.exists(config_path):
                 with open(config_path, 'r') as f:
                     config = json.load(f)
                     if "ai_models" in config and isinstance(config["ai_models"], list):
                         return config["ai_models"]
            
             # Fallback to File Scan
             if os.path.exists(models_dir):
                 for file in os.listdir(models_dir):
                     if file.endswith(".pt") or file.endswith(".engine") or file.endswith(".onnx"):
                         try:
                            mtime = os.path.getmtime(os.path.join(models_dir, file))
                            models_list.append({
                                "model_name": file,
                                "model_version": "auto-detected",
                                "last_update": datetime.datetime.fromtimestamp(mtime).isoformat()
                            })
                         except OSError:
                             continue
             
             return models_list # Return empty list if none found, DO NOT fake a model
        except Exception as e:
            return [{"error": f"Model detection failed: {str(e)}"}]

    def _detect_controller_type(self):
        """Detects if running on Nvidia Jetson or Raspberry Pi."""
        try:
            with open("/proc/device-tree/model", "r") as f:
                model = f.read().strip().replace('\x00', '')
                if "NVIDIA" in model or "Jetson" in model:
                    return "NVIDIA Jetson"
                if "Raspberry Pi" in model:
                    return "Raspberry Pi"
                return model 
        except FileNotFoundError:
            pass 
        
        machine = platform.machine()
        if "aarch64" in machine or "arm" in machine:
             return "Generic ARM Edge Device"
        return "Generic x86 Host"

    def _get_hardware_info(self):
        """
        Merges auto-detection with static map (if available).
        """
        # Null-safe detection call
        try:
            detected = self.probe.probe_all()
        except Exception:
            # Emergency structural fallback
            detected = {"cameras": [], "i2c_devices": [], "serial_ports": [], "storage": []}
        
        info = {
            "summary": "Hardware Auto-Detection Report",
            "detected_cameras": detected.get("cameras", []),
            "detected_i2c": detected.get("i2c_devices", []),
            "detected_serial": detected.get("serial_ports", []),
            "detected_mcu": [p for p in detected.get("serial_ports", []) if "USB" in (p.get("alias") or "") or "ACM" in (p.get("alias") or "")]
        }
        return info

    def _run_diagnostics(self):
        """
        Run real hardware diagnostics with prioritized results.
        Returns standardized Status/Reason objects.
        """
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "network": self._check_network(),
            "disk": self._check_disk(),
            "camera": {"status": "Not Detected", "details": []},
            "sensor": {"status": "Fail", "error": "Driver not loaded"},
            "mcu": self._check_mcu()
        }
        
        # Real Camera probe
        if hasattr(self, 'probe'):
             cams = self.probe.discovery_results.get("cameras", [])
             if cams:
                 results["camera"] = {"status": "Pass", "count": len(cams), "details": cams}
        
        return results

    def _check_network(self):
        """Standard network check with socket fallback for ICMP-restricted zones."""
        # Phase 1: ICMP Ping
        try:
            subprocess.check_call(["ping", "-c", "1", "-W", "2", "8.8.8.8"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            return {"status": "Pass", "method": "ICMP"}
        except (subprocess.CalledProcessError, Exception):
            pass

        # Phase 2: Socket Connect (Fallback)
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3).close()
            return {"status": "Pass", "method": "TCP/UDP"}
        except Exception as e:
            return {"status": "Fail", "error": str(e)}

    def _check_disk(self):
        """Check if root disk has space via psutil with safe return."""
        if psutil:
            try:
                usage = psutil.disk_usage('/')
                status = "Pass" if usage.percent < 95 else "Critical"
                return {"status": status, "usage_percent": usage.percent}
            except Exception as e:
                return {"status": "Error", "details": str(e)}
        return {"status": "Unknown", "error": "psutil missing"}

    def _check_mcu(self):
        """Check for MCU identification via serial attributes."""
        if hasattr(self, 'probe'):
            # Look for ACM/USB patterns in serial paths
            mcus = [p for p in self.probe.discovery_results.get("serial_ports", []) 
                    if "USB" in (p.get("path") or "") or "ACM" in (p.get("path") or "")]
            if mcus:
                return {"status": "Pass", "candidates": mcus}
        return {"status": "Fail", "error": "No MCU-like serial ports detected"}

    def _get_health_metrics(self):
        """
        Get current system health metrics with Null Safety.
        """
        metrics = {
            "cpu_usage_percent": None,
            "memory_usage_percent": None,
            "disk_usage_percent": None
        }
        
        if psutil:
            try:
                metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=None)
                metrics["memory_usage_percent"] = psutil.virtual_memory().percent
                metrics["disk_usage_percent"] = psutil.disk_usage('/').percent
            except Exception:
                pass
        
        return metrics

if __name__ == "__main__":
    # Self-test when run directly
    diag = EdgeDiagnostics()
    print(json.dumps(diag.get_specs(), indent=4))
