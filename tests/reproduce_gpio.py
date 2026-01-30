import os
import sys

# Attempt to set model name BEFORE importing Jetson.GPIO
os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'

try:
    import Jetson.GPIO as GPIO
    print(f"[*] Jetson.GPIO imported successfully!")
    print(f"[*] GPIO Model: {GPIO.model}")
    print(f"[*] GPIO Version: {GPIO.VERSION}")
    
    GPIO.setmode(GPIO.BOARD)
    print("[*] GPIO.setmode(GPIO.BOARD) successful!")
    
    # Try a simple pin setup if possible (using a safe pin like 7)
    # GPIO.setup(7, GPIO.OUT)
    # print("[*] Pin 7 setup as OUT successful!")
    
    GPIO.cleanup()
    print("[*] GPIO Cleanup successful!")
    
except Exception as e:
    print(f"[!] GPIO Test Failed: {e}")
    import traceback
    traceback.print_exc()
