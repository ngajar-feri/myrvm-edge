import os
import subprocess

# Force Jetson model name for Orin Nano compatibility if automatic detection fails
if os.path.exists('/proc/device-tree/model'):
    with open('/proc/device-tree/model', 'r') as f:
        if 'Orin Nano' in f.read():
            os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'

try:
    import RPi.GPIO as GPIO
except ImportError:
    try:
        import Jetson.GPIO as GPIO
    except ImportError:
        GPIO = None

from .base_driver import BaseDriver

class PeripheralDriver(BaseDriver):
    """
    Driver for peripheral feedback (LED status, Audio guidances).
    """
    def __init__(self, name, pin_config=None):
        super().__init__(name)
        self.pins = pin_config

    def initialize(self):
        if GPIO and self.pins:
            GPIO.setwarnings(False)
            try:
                GPIO.setmode(GPIO.BCM)
            except Exception:
                pass
            # Support for simple LED control
            try:
                if 'pin' in self.pins:
                    GPIO.setup(self.pins['pin'], GPIO.OUT)
                    GPIO.output(self.pins['pin'], GPIO.LOW)
            except Exception as e:
                self.logger.error(f"GPIO Setup Error ({self.name}): {e}")
        return super().initialize()

    def set_led(self, state):
        """Sets LED state (True/False)."""
        if GPIO and self.pins and 'pin' in self.pins:
            GPIO.output(self.pins['pin'], GPIO.HIGH if state else GPIO.LOW)

    def play_audio(self, file_path):
        """Plays an audio file using system aplay (Linux standard)."""
        self.logger.info(f"Playing audio: {file_path}")
        if not os.path.exists(file_path):
            self.logger.error("Audio file not found.")
            return False
            
        try:
            # -q for quiet mode
            subprocess.Popen(["aplay", "-q", file_path])
            return True
        except Exception as e:
            self.logger.error(f"Audio playback failed: {e}")
            return False
