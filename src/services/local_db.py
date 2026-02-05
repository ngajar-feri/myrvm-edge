"""
local_db.py - SQLite Database Manager for Offline Transactions

This module handles all SQLite operations for buffering transactions
when the Edge device is offline.
"""

import sqlite3
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalDB")

# Database path
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "local.db"


class LocalDatabase:
    """SQLite database manager for offline transaction storage."""
    
    def __init__(self):
        self.db_path = str(DB_PATH)
        self.system_donation_user_id: Optional[int] = None
        self._ensure_data_dir()
        self._init_db()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "temp_images").mkdir(exist_ok=True)
        logger.info(f"Data directory ensured: {DATA_DIR}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema if tables don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Offline Transactions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                timestamp TEXT NOT NULL,
                synced_at TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Offline Transaction Items Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_transaction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                bottle_type TEXT NOT NULL,
                weight REAL DEFAULT 0,
                points INTEGER DEFAULT 0,
                FOREIGN KEY (transaction_id) REFERENCES offline_transactions(id)
            )
        ''')
        
        # Edge Activity Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edge_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"SQLite database initialized at: {self.db_path}")
    
    # ==================== System Donation User ====================
    
    def set_system_donation_user_id(self, user_id: int):
        """Cache the System Donation user_id from handshake."""
        self.system_donation_user_id = user_id
        logger.info(f"System Donation user_id cached: {user_id}")
    
    def get_system_donation_user_id(self) -> Optional[int]:
        """Get cached System Donation user_id."""
        return self.system_donation_user_id
    
    # ==================== Transaction CRUD ====================
    
    def create_offline_transaction(self, items: List[Dict]) -> Optional[str]:
        """
        Create a new offline transaction with items.
        
        Args:
            items: List of dicts with bottle_type, weight, points
            
        Returns:
            session_id if successful, None otherwise
        """
        if not self.system_donation_user_id:
            logger.error("Cannot create transaction: System Donation user_id not set")
            return None
        
        session_id = f"offline-{uuid.uuid4()}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert transaction
            cursor.execute('''
                INSERT INTO offline_transactions (session_id, user_id, status, timestamp)
                VALUES (?, ?, 'pending', ?)
            ''', (session_id, self.system_donation_user_id, timestamp))
            
            transaction_id = cursor.lastrowid
            
            # Insert items
            for item in items:
                cursor.execute('''
                    INSERT INTO offline_transaction_items 
                    (transaction_id, bottle_type, weight, points)
                    VALUES (?, ?, ?, ?)
                ''', (
                    transaction_id,
                    item.get('bottle_type', 'unknown'),
                    item.get('weight', 0),
                    item.get('points', 0)
                ))
            
            conn.commit()
            logger.info(f"Offline transaction created: {session_id} with {len(items)} items")
            
            # Log activity
            self.log_activity('transaction_created', 'completed', f"Session: {session_id}")
            
            return session_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create offline transaction: {e}")
            return None
        finally:
            conn.close()
    
    def get_pending_transactions(self) -> List[Dict]:
        """Get all pending transactions for sync."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, user_id, timestamp 
            FROM offline_transactions 
            WHERE status = 'pending'
            ORDER BY created_at ASC
        ''')
        
        transactions = []
        for row in cursor.fetchall():
            # Get items for this transaction
            cursor.execute('''
                SELECT bottle_type, weight, points 
                FROM offline_transaction_items 
                WHERE transaction_id = ?
            ''', (row['id'],))
            
            items = [dict(item) for item in cursor.fetchall()]
            
            transactions.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'timestamp': row['timestamp'],
                'items': items
            })
        
        conn.close()
        return transactions
    
    def mark_transactions_synced(self, transaction_ids: List[int]):
        """Mark transactions as synced after successful upload."""
        if not transaction_ids:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        synced_at = datetime.utcnow().isoformat() + "Z"
        placeholders = ','.join('?' * len(transaction_ids))
        
        cursor.execute(f'''
            UPDATE offline_transactions 
            SET status = 'synced', synced_at = ?
            WHERE id IN ({placeholders})
        ''', [synced_at] + transaction_ids)
        
        conn.commit()
        conn.close()
        logger.info(f"Marked {len(transaction_ids)} transactions as synced")
    
    def get_pending_count(self) -> int:
        """Get count of pending transactions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM offline_transactions WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    # ==================== Activity Logging ====================
    
    def log_activity(self, event_type: str, status: str = 'pending', details: str = None):
        """Log an edge activity event."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO edge_activity_logs (event_type, status, details)
            VALUES (?, ?, ?)
        ''', (event_type, status, details))
        
        conn.commit()
        conn.close()
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent activity logs."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM edge_activity_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs


# Singleton instance
_db_instance: Optional[LocalDatabase] = None

def get_local_db() -> LocalDatabase:
    """Get or create the singleton LocalDatabase instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = LocalDatabase()
    return _db_instance
