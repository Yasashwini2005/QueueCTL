import sqlite3
import json
from datetime import datetime
from pathlib import Path
import threading

class Database:
    """Handles all database operations with thread-safe connections"""
    
    def __init__(self, db_path="data/queuectl.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # Thread-local storage for connections
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Jobs table with bonus features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                state TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_retry_at TEXT,
                error_message TEXT,
                output TEXT,
                priority INTEGER DEFAULT 0,
                timeout INTEGER DEFAULT 300,
                run_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                execution_time REAL
            )
        ''')
        
        # Configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Worker tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id TEXT PRIMARY KEY,
                pid INTEGER NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                current_job_id TEXT
            )
        ''')
        
        # Metrics table (NEW)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT
            )
        ''')
        
        conn.commit()
    
    def execute_query(self, query, params=()):
        """Execute a query and return results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    def fetch_one(self, query, params=()):
        """Fetch single row"""
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query, params=()):
        """Fetch all rows"""
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
