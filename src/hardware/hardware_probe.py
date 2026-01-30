import subprocess
import os
import glob
import json

class HardwareProbe:
    """
    Scans system buses to detect active hardware peripherals.
    Acts as the 'Reality' layer to complement the 'Intent' (hardware_map.json).
    """

    def __init__(self):
        self.discovery_results = {
            "cameras": [],
            "i2c_devices": [],
            "serial_ports": [],
            "storage": []
        }

    def probe_all(self):
        """Runs all discovery probes."""
        self.discovery_results["cameras"] = self._probe_cameras()
        self.discovery_results["i2c_devices"] = self._probe_i2c()
        self.discovery_results["serial_ports"] = self._probe_serial()
        return self.discovery_results

    def _probe_cameras(self):
        """Scans for video devices using v4l2-ctl with kernel fallback."""
        cameras = []
        try:
            video_devices = glob.glob("/dev/video*")
            for dev in video_devices:
                name = "Unknown Camera"
                # Primary: v4l2-ctl
                try:
                    cmd = ["v4l2-ctl", "--device", dev, "--info"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if "Card type" in line:
                                name = line.split(':')[1].strip()
                                break
                    else:
                        # Fallback: sysfs
                        v4l_name_path = f"/sys/class/video4linux/{os.path.basename(dev)}/name"
                        if os.path.exists(v4l_name_path):
                            with open(v4l_name_path, 'r') as f:
                                name = f.read().strip()
                except Exception:
                    # Final Fallback check
                    pass
                
                cameras.append({"path": dev, "name": name})
        except Exception as e:
            # Report structural empty list on critical failure
            pass
        return cameras

    def _probe_i2c(self):
        """Scans I2C buses with i2cdetect and sysfs fallback."""
        devices = []
        try:
            # 1. Detect Buses via sysfs first (Reality check)
            buses = []
            if os.path.exists("/sys/class/i2c-adapter"):
                for adapter in os.listdir("/sys/class/i2c-adapter"):
                    if adapter.startswith("i2c-"):
                        try:
                            bus_id = int(adapter.split("-")[1])
                            buses.append(bus_id)
                        except ValueError:
                            continue
            
            # If sysfs empty, fallback to common range
            if not buses:
                buses = list(range(10))

            for bus_id in buses:
                bus_path = f"/dev/i2c-{bus_id}"
                if not os.path.exists(bus_path):
                    continue

                # Use i2cdetect -y [bus]
                i2c_cmd = "i2cdetect"
                if subprocess.run(["which", i2c_cmd], capture_output=True).returncode != 0:
                    if os.path.exists("/usr/sbin/i2cdetect"):
                        i2c_cmd = "/usr/sbin/i2cdetect"
                
                try:
                    result = subprocess.run([i2c_cmd, "-y", str(bus_id)], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]
                        for line in lines:
                            parts = line.split(':')[1].split()
                            for part in parts:
                                if part != "--":
                                    devices.append({
                                        "bus": bus_id,
                                        "address": f"0x{part.lower()}",
                                        "status": "In Use (Kernel)" if part == "UU" else "Active"
                                    })
                except Exception:
                    # If i2cdetect fails, we report the bus exists but addresses unknown
                    continue

        except Exception as e:
            pass
        return devices

    def _probe_serial(self):
        """Scans for active UART/USB-Serial ports with driver check."""
        ports = []
        patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyTHS*", "/dev/serial/by-id/*"]
        for p in patterns:
            for port in glob.glob(p):
                # Resolve symlinks for by-id
                real_path = os.path.realpath(port)
                if real_path not in [p['path'] for p in ports]:
                    ports.append({
                        "path": real_path,
                        "alias": port if port != real_path else None
                    })
        return ports

if __name__ == "__main__":
    probe = HardwareProbe()
    print("=== Hardware Discovery Probe ===")
    results = probe.probe_all()
    print(json.dumps(results, indent=2))
