from .database import Database

class Config:
    """Configuration management"""
    
    DEFAULTS = {
        'max_retries': '3',
        'backoff_base': '2',
        'worker_poll_interval': '2',
        'job_timeout': '300'
    }
    
    def __init__(self, db_path="data/queuectl.db"):
        self.db = Database(db_path)
        self._init_defaults()
    
    def _init_defaults(self):
        """Initialize default configuration"""
        for key, value in self.DEFAULTS.items():
            existing = self.db.fetch_one(
                'SELECT value FROM config WHERE key=?', (key,)
            )
            if not existing:
                self.db.execute_query(
                    'INSERT INTO config (key, value) VALUES (?, ?)',
                    (key, value)
                )
    
    def get(self, key, default=None):
        """Get configuration value"""
        row = self.db.fetch_one('SELECT value FROM config WHERE key=?', (key,))
        if row:
            return row['value']
        return default or self.DEFAULTS.get(key)
    
    def set(self, key, value):
        """Set configuration value"""
        existing = self.db.fetch_one('SELECT value FROM config WHERE key=?', (key,))
        if existing:
            self.db.execute_query(
                'UPDATE config SET value=? WHERE key=?',
                (str(value), key)
            )
        else:
            self.db.execute_query(
                'INSERT INTO config (key, value) VALUES (?, ?)',
                (key, str(value))
            )
    
    def get_all(self):
        """Get all configuration"""
        rows = self.db.fetch_all('SELECT key, value FROM config')
        return {row['key']: row['value'] for row in rows}