import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger("BrowserManager")

class BrowserManager:
    """Manages the lifecycle of the kiosk browser."""
    
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        self.launch_script = self.base_dir / "scripts" / "launch_kiosk.sh"
        self.process = None

    def launch_kiosk(self, url, browser_pref="auto"):
        """Executes the kiosk browser in the background."""
        if not self.launch_script.exists():
            logger.error(f"Launch script not found: {self.launch_script}")
            return False

        # Ensure executable permission
        if not os.access(self.launch_script, os.X_OK):
            os.chmod(self.launch_script, 0o755)

        cmd = ["bash", str(self.launch_script), url, browser_pref]

        try:
            logger.info(f"Launching Kiosk Browser at: {url}")
            # Use setsid so browser doesn't die when main app restarts
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid 
            )
            return True
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return False

    def close_kiosk(self):
        """Force close the browser process if needed."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 15) # SIGTERM
                self.process = None
                return True
            except Exception as e:
                logger.error(f"Failed to stop browser: {e}")
        return False
