import json
import os
from .motor_driver import StepperDriver
from .sensor_driver import SensorDriver
from .peripheral_driver import PeripheralDriver
from .hardware_probe import HardwareProbe

class HardwareManager:
    """
    Orchestrates all hardware drivers based on the hardware_map.json configuration.
    """
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../../config/hardware_map.json')
        
        self.drivers = {}
        self.load_config(config_path)

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            
            # 1. Initialize Motors
            for act in config.get('actuators', []):
                if 'motor' in act['name']:
                    model = act.get('model', 'nema17')
                    self.drivers[act['name']] = StepperDriver(act['friendly_name'], act['pins'], model=model)

            # 2. Initialize Sensors
            for sen in config.get('sensors', []):
                s_type = "ultrasonic" if "ultrasonic" in sen['name'] else "proximity"
                self.drivers[sen['name']] = SensorDriver(sen['friendly_name'], sen, sensor_type=s_type)

            # 3. Initialize Peripherals
            self.drivers['status_led'] = PeripheralDriver("Status LED", {'pin': 10})
            self.drivers['audio'] = PeripheralDriver("Audio Guidance")

        except Exception as e:
            print(f"[!] HardwareManager init error: {e}")

    def initialize_all(self):
        for name, driver in self.drivers.items():
            driver.initialize()

    def get_driver(self, name):
        return self.drivers.get(name)

    def get_discovery_report(self):
        """
        Runs a dynamic probe and compares it with the configured intent.
        """
        probe = HardwareProbe()
        reality = probe.probe_all()
        
        return {
            "reality": reality,
            "configured_count": len(self.drivers),
            "healthy_count": sum(1 for d in self.drivers.values() if d.is_initialized)
        }

    def cleanup(self):
        for driver in self.drivers.values():
            driver.cleanup()
