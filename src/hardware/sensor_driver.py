import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    try:
        import Jetson.GPIO as GPIO
    except ImportError:
        GPIO = None

from .base_driver import BaseDriver

class SensorDriver(BaseDriver):
    """
    Driver for sensors (Ultrasonic HC-SR04, IR Proximity, DHT22).
    """
    def __init__(self, name, pin_config, sensor_type="ultrasonic"):
        super().__init__(name)
        self.pins = pin_config
        self.sensor_type = sensor_type.lower()

    def initialize(self):
        if GPIO is None:
            return False
            
        GPIO.setwarnings(False)
        try:
            GPIO.setmode(GPIO.BCM)
        except Exception:
            pass # Ignore mode setting errors if already set

        try:
            if self.sensor_type == "ultrasonic":
                # Access nested 'pins' dict for ultrasonic
                p = self.pins.get('pins', {})
                GPIO.setup(p.get('trigger'), GPIO.OUT)
                GPIO.setup(p.get('echo'), GPIO.IN)
                GPIO.output(p.get('trigger'), GPIO.LOW)
            elif self.sensor_type == "proximity":
                # Access 'pin' directly or from 'pins' dict
                p_pin = self.pins.get('pin') or self.pins.get('pins', {}).get('pin')
                if p_pin:
                    GPIO.setup(p_pin, GPIO.IN)
        except Exception as e:
            print(f"[!] GPIO Setup Error ({self.name}): {e}")
            # Continue execution even if GPIO fails, to allow handshake to persist
            
        return super().initialize()

    def read(self):
        """Reads data from the sensor."""
        if not self.is_initialized:
            return None

        if self.sensor_type == "ultrasonic":
            p = self.pins.get('pins', {})
            trigger_pin = p.get('trigger')
            echo_pin = p.get('echo')
            
            if not trigger_pin or not echo_pin:
                return None

            # Pulse trigger
            GPIO.output(trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(trigger_pin, GPIO.LOW)

            start_time = time.time()
            stop_time = time.time()

            # Record echo start/stop
            timeout = time.time() + 0.1
            while GPIO.input(echo_pin) == 0:
                start_time = time.time()
                if start_time > timeout: return None
                
            while GPIO.input(echo_pin) == 1:
                stop_time = time.time()
                if stop_time > timeout: return None

            # Distance calculation (sound speed 34300 cm/s)
            elapsed = stop_time - start_time
            distance = (elapsed * 34300) / 2
            return round(distance, 2)

        elif self.sensor_type == "proximity":
            # Returns True if object detected (active level check)
            active_level = self.pins.get('active_level', 'LOW')
            val = GPIO.input(self.pins['pin'])
            return val == (GPIO.LOW if active_level == 'LOW' else GPIO.HIGH)

        return None
