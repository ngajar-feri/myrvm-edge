#!/usr/bin/env python3
"""
Mock Handshake Test - Tests handshake with placeholder data
Uses mock values when actual hardware is not detected.

Run: python tests/test_handshake_mock.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.api_client import RvmApiClient

# Mock configuration - these would come from credentials.json in production
MOCK_CONFIG = {
    "base_url": "https://myrvm.penelitian.my.id/api/v1",
    "api_key": "MOCK_API_KEY_FOR_TESTING",
    "device_id": "MOCK-ORIN-SN-12345678",
    "name": "MOCK RVM Test Unit"
}


def get_mock_system_info():
    """Return mock system info when hardware is not available."""
    return {
        "jetpack_version": "MOCK-6.0",
        "firmware_version": "MOCK-v1.0.0",
        "python_version": "3.10.12",
        "ai_models": {
            "model_name": "MOCK-best.pt",
            "model_version": "MOCK-v1.0.0-beta",
            "hash": "MOCK-a1b2c3d4e5f6",
            "last_update": "2026-01-27T00:00:00Z"
        }
    }


def get_mock_hardware_info():
    """Return mock hardware info when devices are not detected."""
    return {
        "microcontroller": {
            "type": "MOCK-ESP32",
            "connection": "MOCK-UART",
            "port": "/dev/MOCK-ttyTHS1",
            "baud_rate": 115200,
            "status": "MOCK-connected"
        },
        "cameras": [
            {
                "id": 0,
                "path": "/dev/MOCK-video0",
                "name": "MOCK Logitech C920",
                "connection_type": "MOCK-USB",
                "physical_location": "MOCK-usb-1.4:1.0",
                "serial_number": "MOCK-SN-8F21",
                "status": "MOCK-ready",
                "capabilities": {
                    "max_resolution": "1920x1080",
                    "format": "MJPG",
                    "fps": 30
                },
                "role": "object_detection"
            }
        ],
        "sensors": [
            {
                "name": "MOCK_bin_ultrasonic",
                "friendly_name": "MOCK Sensor Level Bak",
                "model": "MOCK-HC-SR04",
                "interface": "GPIO",
                "pins": {"trigger": 12, "echo": 13},
                "status": "MOCK-online",
                "last_reading": "50",
                "unit": "cm"
            },
            {
                "name": "MOCK_intake_proximity",
                "friendly_name": "MOCK Sensor Deteksi Masuk",
                "model": "MOCK-IR-Obstacle",
                "interface": "GPIO",
                "pin": 18,
                "active_level": "LOW",
                "status": "MOCK-online",
                "last_reading": "0",
                "unit": "boolean"
            },
            {
                "name": "MOCK_internal_temp",
                "friendly_name": "MOCK Sensor Suhu Internal",
                "model": "MOCK-DHT22",
                "interface": "GPIO",
                "pin": 4,
                "status": "MOCK-online",
                "last_reading": "28.5",
                "unit": "°C"
            }
        ],
        "actuators": [
            {
                "name": "MOCK_sorting_motor",
                "friendly_name": "MOCK Motor Pemilah",
                "model": "MOCK-Stepper-NEMA17",
                "interface": "GPIO",
                "driver": "TB6600",
                "pins": {"step": 23, "dir": 24, "enable": 25},
                "status": "MOCK-ok"
            },
            {
                "name": "MOCK_door_lock",
                "friendly_name": "MOCK Kunci Pintu",
                "model": "MOCK-Solenoid-12V",
                "interface": "GPIO",
                "pin": 27,
                "status": "MOCK-ok"
            },
            {
                "name": "MOCK_status_led",
                "friendly_name": "MOCK Lampu Indikator",
                "model": "MOCK-RGB-LED-Strip",
                "interface": "GPIO",
                "pin": 10,
                "last_reading": "green",
                "status": "MOCK-ok"
            }
        ]
    }


def get_mock_diagnostics():
    """Return mock diagnostics results."""
    return {
        "network_check": "MOCK-pass",
        "camera_check": "MOCK-pass",
        "motor_test": "MOCK-skip",
        "ai_inference_test": "MOCK-skip"
    }


def get_mock_health_metrics():
    """Return mock health metrics."""
    return {
        "cpu_usage_percent": 15.5,
        "memory_usage_percent": 42.0,
        "disk_usage_percent": 12.8,
        "cpu_temperature": 45.0
    }


def build_mock_payload():
    """Build complete mock handshake payload."""
    return {
        # 1. Identity
        "hardware_id": MOCK_CONFIG["device_id"],
        "name": MOCK_CONFIG["name"],
        
        # 2. Network
        "ip_local": "192.168.1.100",
        "ip_vpn": "100.123.143.87",
        "timezone": "Asia/Jakarta",
        
        # 3. System
        "system": get_mock_system_info(),
        
        # 4. Hardware Info
        "hardware_info": get_mock_hardware_info(),
        
        # 5. Diagnostics
        "diagnostics": get_mock_diagnostics(),
        
        # 6. Health Metrics
        "health_metrics": get_mock_health_metrics(),
        
        # Legacy flat fields
        "controller_type": "MOCK-NVIDIA Jetson Orin Nano"
    }


def print_payload(payload, indent=0):
    """Pretty print the payload structure."""
    import json
    print("\n" + "=" * 60)
    print("[MOCK] Complete Handshake Payload:")
    print("=" * 60)
    print(json.dumps(payload, indent=2))


def test_mock_handshake():
    """Test handshake with mock data."""
    print("\n" + "=" * 60)
    print("[MOCK TEST] Handshake Format Verification")
    print("=" * 60)
    
    # Build mock payload
    payload = build_mock_payload()
    print_payload(payload)
    
    # Verify structure
    print("\n" + "-" * 60)
    print("[MOCK] Structure Verification:")
    print("-" * 60)
    
    checks = [
        ("hardware_id", payload.get("hardware_id")),
        ("name", payload.get("name")),
        ("ip_local", payload.get("ip_local")),
        ("ip_vpn", payload.get("ip_vpn")),
        ("timezone", payload.get("timezone")),
        ("system.jetpack_version", payload.get("system", {}).get("jetpack_version")),
        ("system.ai_models.model_name", payload.get("system", {}).get("ai_models", {}).get("model_name")),
        ("hardware_info.microcontroller.type", payload.get("hardware_info", {}).get("microcontroller", {}).get("type")),
        ("hardware_info.cameras", len(payload.get("hardware_info", {}).get("cameras", []))),
        ("hardware_info.sensors", len(payload.get("hardware_info", {}).get("sensors", []))),
        ("hardware_info.actuators", len(payload.get("hardware_info", {}).get("actuators", []))),
        ("diagnostics.network_check", payload.get("diagnostics", {}).get("network_check")),
        ("health_metrics.cpu_usage_percent", payload.get("health_metrics", {}).get("cpu_usage_percent")),
    ]
    
    for field, value in checks:
        status = "✅" if value else "❌"
        print(f"  {status} {field}: {value}")
    
    print("\n" + "=" * 60)
    print("[MOCK TEST] Complete!")
    print("=" * 60)
    
    return payload


if __name__ == "__main__":
    test_mock_handshake()
