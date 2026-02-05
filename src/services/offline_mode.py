"""
offline_mode.py - Offline Mode Controller

This module manages the Edge device's online/offline state transitions
based on heartbeat/handshake success or failure.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Callable, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OfflineMode")


class EdgeMode(Enum):
    """Edge device operational modes."""
    ONLINE = "online"              # Full functionality, connected to server
    OFFLINE_GUEST = "offline_guest"  # Offline, only donation mode available
    TRANSITIONING = "transitioning"  # Currently switching modes


class OfflineModeController:
    """
    Controls the Edge device's online/offline state.
    
    Monitors heartbeat status and triggers mode transitions when
    the connection to the server is lost or restored.
    """
    
    def __init__(self):
        self.current_mode: EdgeMode = EdgeMode.TRANSITIONING
        self.system_donation_user_id: Optional[int] = None
        self.last_heartbeat_success: Optional[datetime] = None
        self.consecutive_failures: int = 0
        self.max_failures_before_offline: int = 3
        
        # Callbacks for mode changes
        self._on_mode_change_callbacks: List[Callable] = []
        self._on_reconnect_callbacks: List[Callable] = []
        
        logger.info("OfflineModeController initialized")
    
    # ==================== Mode Management ====================
    
    def get_current_mode(self) -> EdgeMode:
        """Get the current operational mode."""
        return self.current_mode
    
    def is_online(self) -> bool:
        """Check if device is in online mode."""
        return self.current_mode == EdgeMode.ONLINE
    
    def is_offline(self) -> bool:
        """Check if device is in offline guest mode."""
        return self.current_mode == EdgeMode.OFFLINE_GUEST
    
    def _set_mode(self, new_mode: EdgeMode, reason: str = ""):
        """
        Internal method to set the mode and trigger callbacks.
        
        Args:
            new_mode: The new mode to set
            reason: Reason for the mode change (for logging)
        """
        if new_mode == self.current_mode:
            return
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        logger.info(f"Mode changed: {old_mode.value} -> {new_mode.value} | Reason: {reason}")
        
        # Trigger callbacks
        for callback in self._on_mode_change_callbacks:
            try:
                callback(old_mode, new_mode, reason)
            except Exception as e:
                logger.error(f"Mode change callback error: {e}")
    
    # ==================== Heartbeat Handling ====================
    
    def on_heartbeat_success(self, response_data: dict = None):
        """
        Called when a heartbeat/handshake to the server succeeds.
        
        Args:
            response_data: Optional response data from server containing user_id etc.
        """
        self.last_heartbeat_success = datetime.now()
        self.consecutive_failures = 0
        
        # Cache System Donation user_id from handshake response
        if response_data:
            user_id = response_data.get('system_donation_user_id')
            if user_id:
                self.system_donation_user_id = user_id
                logger.info(f"System Donation user_id saved: {user_id}")
        
        # Transition to online if was offline
        if self.current_mode == EdgeMode.OFFLINE_GUEST:
            self._set_mode(EdgeMode.ONLINE, "Connection restored")
            
            # Trigger reconnect callbacks (for sync)
            for callback in self._on_reconnect_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Reconnect callback error: {e}")
        
        elif self.current_mode == EdgeMode.TRANSITIONING:
            self._set_mode(EdgeMode.ONLINE, "Initial connection established")
    
    def on_heartbeat_failure(self, error: str = ""):
        """
        Called when a heartbeat/handshake to the server fails.
        
        Args:
            error: Optional error message
        """
        self.consecutive_failures += 1
        
        logger.warning(f"Heartbeat failed ({self.consecutive_failures}/{self.max_failures_before_offline}): {error}")
        
        # Transition to offline after max failures
        if self.consecutive_failures >= self.max_failures_before_offline:
            if self.current_mode != EdgeMode.OFFLINE_GUEST:
                self._set_mode(
                    EdgeMode.OFFLINE_GUEST, 
                    f"Connection lost after {self.consecutive_failures} failures"
                )
    
    def on_connection_lost(self):
        """Called when WebSocket connection is completely lost."""
        logger.warning("WebSocket connection lost - entering offline mode immediately")
        self._set_mode(EdgeMode.OFFLINE_GUEST, "WebSocket disconnected")
        self.consecutive_failures = self.max_failures_before_offline
    
    # ==================== System Donation User ====================
    
    def get_system_donation_user_id(self) -> Optional[int]:
        """Get the cached System Donation user_id."""
        return self.system_donation_user_id
    
    def has_system_donation_user_id(self) -> bool:
        """Check if System Donation user_id is available."""
        return self.system_donation_user_id is not None
    
    # ==================== Callbacks ====================
    
    def on_mode_change(self, callback: Callable):
        """
        Register a callback for mode changes.
        
        Callback signature: (old_mode: EdgeMode, new_mode: EdgeMode, reason: str)
        """
        self._on_mode_change_callbacks.append(callback)
    
    def on_reconnect(self, callback: Callable):
        """
        Register a callback for when connection is restored.
        
        Callback signature: ()
        
        Useful for triggering sync operations.
        """
        self._on_reconnect_callbacks.append(callback)
    
    # ==================== Status Report ====================
    
    def get_status(self) -> dict:
        """Get current status as a dictionary."""
        return {
            "mode": self.current_mode.value,
            "is_online": self.is_online(),
            "system_donation_user_id": self.system_donation_user_id,
            "last_heartbeat": self.last_heartbeat_success.isoformat() if self.last_heartbeat_success else None,
            "consecutive_failures": self.consecutive_failures
        }


# Singleton instance
_controller_instance: Optional[OfflineModeController] = None

def get_offline_controller() -> OfflineModeController:
    """Get or create the singleton OfflineModeController instance."""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = OfflineModeController()
    return _controller_instance
