import time
import os

# Force Jetson model name for Orin Nano compatibility if automatic detection fails
if os.path.exists('/proc/device-tree/model'):
    with open('/proc/device-tree/model', 'r') as f:
        if 'Orin Nano' in f.read():
            os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Fallback for Jetson or non-RPi environments
    try:
        import Jetson.GPIO as GPIO
    except ImportError:
        GPIO = None

from .base_driver import BaseDriver

class StepperDriver(BaseDriver):
    """
    Driver for Stepper Motors (NEMA17 with TB6600 or 28BYJ-48 with ULN2003).
    """
    def __init__(self, name, pins, model="nema17"):
        super().__init__(name)
        self.pins = pins
        self.model = model.lower()
        
        # 28BYJ-48 specific sequence (4 phases)
        self.step_sequence = [
            [1, 0, 0, 1],
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1]
        ]

    def initialize(self):
        if GPIO is None:
            self.logger.error("GPIO library not found. Running in simulation mode.")
            return False
            
        GPIO.setwarnings(False)
        try:
            GPIO.setmode(GPIO.BCM)
        except Exception:
            pass

        try:
            if self.model == "nema17":
                # TB6600 needs Step, Dir, Enable
                GPIO.setup(self.pins['step'], GPIO.OUT)
                GPIO.setup(self.pins['dir'], GPIO.OUT)
                if 'enable' in self.pins:
                    GPIO.setup(self.pins['enable'], GPIO.OUT)
                    GPIO.output(self.pins['enable'], GPIO.LOW) # Often Active LOW
            else:
                # 28BYJ-48 needs 4 phase pins
                for pin in self.pins.values():
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
        except Exception as e:
            self.logger.error(f"GPIO Setup Error ({self.name}): {e}")
                
        return super().initialize()

    def move(self, steps, direction=1, speed=0.001):
        """
        Moves the motor.
        direction: 1 (CW), 0 (CCW)
        speed: delay between steps
        """
        if not self.is_initialized:
            self.logger.warning("Driver not initialized.")
            return

        if self.model == "nema17":
            GPIO.output(self.pins['dir'], direction)
            for _ in range(abs(steps)):
                GPIO.output(self.pins['step'], GPIO.HIGH)
                time.sleep(speed)
                GPIO.output(self.pins['step'], GPIO.LOW)
                time.sleep(speed)
        else:
            # 28BYJ-48 Half-step sequence
            step_count = len(self.step_sequence)
            direction_multiplier = 1 if direction == 1 else -1
            
            for i in range(abs(steps)):
                for pin_idx, pin in enumerate(list(self.pins.values())):
                    # Use sequence index correctly
                    GPIO.output(pin, self.step_sequence[i % step_count][pin_idx])
                time.sleep(speed)

    def cleanup(self):
        if GPIO:
            if self.model == "nema17":
                GPIO.output(self.pins['step'], GPIO.LOW)
            else:
                for pin in self.pins.values():
                    GPIO.output(pin, GPIO.LOW)
        super().cleanup()
