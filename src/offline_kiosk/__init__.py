"""
Offline Kiosk Module

Provides local frontend for Edge device when offline.
"""

from .app import app, start_offline_kiosk

__all__ = ['app', 'start_offline_kiosk']
