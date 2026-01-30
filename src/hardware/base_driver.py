import logging

class BaseDriver:
    """
    Base class for all hardware drivers to ensure consistent logging and interface.
    """
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(f"Driver.{name}")
        self.is_initialized = False

    def initialize(self):
        """Initializes the physical hardware pins."""
        self.logger.info(f"Initializing {self.name}...")
        self.is_initialized = True
        return True

    def cleanup(self):
        """Safely releases hardware resources."""
        self.logger.info(f"Cleaning up {self.name}...")
        self.is_initialized = False
