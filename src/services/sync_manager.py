"""
sync_manager.py - Store-and-Forward Sync Manager

This module handles synchronization of offline transactions
to the server when connection is restored.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, List, Dict
from datetime import datetime

from .local_db import get_local_db
from .offline_mode import get_offline_controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SyncManager")


class SyncManager:
    """
    Manages synchronization of offline transactions to the server.
    
    Implements store-and-forward pattern: transactions are stored locally
    when offline, then bulk-synced when connection is restored.
    """
    
    def __init__(self, server_url: str, api_token: str):
        self.server_url = server_url.rstrip('/')
        self.api_token = api_token
        self.sync_endpoint = f"{self.server_url}/api/v1/edge/sync-offline"
        self.is_syncing = False
        
        # Register reconnect callback
        controller = get_offline_controller()
        controller.on_reconnect(self._on_reconnect)
        
        logger.info(f"SyncManager initialized with endpoint: {self.sync_endpoint}")
    
    def _on_reconnect(self):
        """Callback triggered when connection is restored."""
        logger.info("Reconnect detected - triggering sync")
        asyncio.create_task(self.sync_offline_transactions())
    
    async def sync_offline_transactions(self) -> Dict:
        """
        Sync all pending offline transactions to the server.
        
        Returns:
            Dict with sync results
        """
        if self.is_syncing:
            logger.warning("Sync already in progress, skipping")
            return {"status": "skipped", "reason": "sync_in_progress"}
        
        self.is_syncing = True
        db = get_local_db()
        
        try:
            # Get pending transactions
            pending = db.get_pending_transactions()
            
            if not pending:
                logger.info("No pending transactions to sync")
                return {"status": "success", "synced_count": 0}
            
            logger.info(f"Syncing {len(pending)} pending transactions...")
            db.log_activity('sync_start', 'pending', f"Syncing {len(pending)} transactions")
            
            # Prepare payload
            payload = {
                "transactions": [
                    {
                        "session_id": t['session_id'],
                        "user_id": t['user_id'],
                        "timestamp": t['timestamp'],
                        "items": [
                            {
                                "type": item['bottle_type'],
                                "weight": item['weight'],
                                "points": item['points']
                            }
                            for item in t['items']
                        ]
                    }
                    for t in pending
                ]
            }
            
            # Send to server
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_token}"
                }
                
                async with session.post(
                    self.sync_endpoint, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        synced_count = result.get('synced_count', len(pending))
                        
                        # Mark transactions as synced
                        transaction_ids = [t['id'] for t in pending]
                        db.mark_transactions_synced(transaction_ids)
                        
                        db.log_activity(
                            'sync_complete', 
                            'completed', 
                            f"Synced {synced_count} transactions"
                        )
                        
                        logger.info(f"Sync complete: {synced_count} transactions synced")
                        return {"status": "success", "synced_count": synced_count}
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Sync failed with status {response.status}: {error_text}")
                        db.log_activity('sync_failed', 'pending', f"HTTP {response.status}")
                        return {"status": "error", "reason": f"HTTP {response.status}"}
        
        except asyncio.TimeoutError:
            logger.error("Sync timed out")
            db.log_activity('sync_timeout', 'pending', "Request timed out")
            return {"status": "error", "reason": "timeout"}
        
        except aiohttp.ClientError as e:
            logger.error(f"Sync connection error: {e}")
            db.log_activity('sync_error', 'pending', str(e))
            return {"status": "error", "reason": str(e)}
        
        except Exception as e:
            logger.error(f"Sync unexpected error: {e}")
            db.log_activity('sync_error', 'pending', str(e))
            return {"status": "error", "reason": str(e)}
        
        finally:
            self.is_syncing = False
    
    async def get_sync_status(self) -> Dict:
        """Get current sync status."""
        db = get_local_db()
        pending_count = db.get_pending_count()
        
        return {
            "is_syncing": self.is_syncing,
            "pending_count": pending_count,
            "last_sync_logs": db.get_recent_logs(5)
        }


# Singleton instance
_sync_manager_instance: Optional[SyncManager] = None

def init_sync_manager(server_url: str, api_token: str) -> SyncManager:
    """Initialize the singleton SyncManager with server credentials."""
    global _sync_manager_instance
    _sync_manager_instance = SyncManager(server_url, api_token)
    return _sync_manager_instance

def get_sync_manager() -> Optional[SyncManager]:
    """Get the singleton SyncManager instance."""
    return _sync_manager_instance
