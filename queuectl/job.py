from datetime import datetime, timedelta
import uuid

class Job:
    """Represents a background job with bonus features"""
    
    STATES = ['pending', 'processing', 'completed', 'failed', 'dead']
    
    def __init__(self, id=None, command=None, state='pending', 
                 attempts=0, max_retries=3, created_at=None, 
                 updated_at=None, next_retry_at=None, 
                 error_message=None, output=None,
                 priority=0, timeout=300, run_at=None,
                 started_at=None, completed_at=None, execution_time=None):
        self.id = id or str(uuid.uuid4())
        self.command = command
        self.state = state
        self.attempts = attempts
        self.max_retries = max_retries
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
        self.next_retry_at = next_retry_at
        self.error_message = error_message
        self.output = output
        # Bonus features
        self.priority = priority  # Higher number = higher priority
        self.timeout = timeout  # Per-job timeout in seconds
        self.run_at = run_at  # Scheduled/delayed execution
        self.started_at = started_at
        self.completed_at = completed_at
        self.execution_time = execution_time
    
    @classmethod
    def from_dict(cls, data):
        """Create Job from dictionary"""
        return cls(
            id=data.get('id'),
            command=data.get('command'),
            state=data.get('state', 'pending'),
            attempts=data.get('attempts', 0),
            max_retries=data.get('max_retries', 3),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            next_retry_at=data.get('next_retry_at'),
            error_message=data.get('error_message'),
            output=data.get('output'),
            priority=data.get('priority', 0),
            timeout=data.get('timeout', 300),
            run_at=data.get('run_at'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            execution_time=data.get('execution_time')
        )
    
    @classmethod
    def from_db_row(cls, row):
        """Create Job from database row (sqlite3.Row object)"""
        # Helper to safely get values from sqlite3.Row
        def safe_get(row, key, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default
        
        return cls(
            id=row['id'],
            command=row['command'],
            state=row['state'],
            attempts=row['attempts'],
            max_retries=row['max_retries'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            next_retry_at=row['next_retry_at'],
            error_message=row['error_message'],
            output=row['output'],
            priority=safe_get(row, 'priority', 0),
            timeout=safe_get(row, 'timeout', 300),
            run_at=safe_get(row, 'run_at'),
            started_at=safe_get(row, 'started_at'),
            completed_at=safe_get(row, 'completed_at'),
            execution_time=safe_get(row, 'execution_time')
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'command': self.command,
            'state': self.state,
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'next_retry_at': self.next_retry_at,
            'error_message': self.error_message,
            'output': self.output,
            'priority': self.priority,
            'timeout': self.timeout,
            'run_at': self.run_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'execution_time': self.execution_time
        }
    
    def calculate_retry_delay(self, base=2):
        """Calculate exponential backoff delay in seconds"""
        return base ** self.attempts
    
    def should_retry(self):
        """Check if job should be retried"""
        return self.attempts < self.max_retries
    
    def is_ready_to_run(self):
        """Check if job is ready to run (respects run_at)"""
        if not self.run_at:
            return True
        return datetime.utcnow().isoformat() >= self.run_at
    
    def mark_for_retry(self, error_msg, backoff_base=2):
        """Prepare job for retry with exponential backoff"""
        self.attempts += 1
        self.error_message = error_msg
        self.updated_at = datetime.utcnow().isoformat()
        
        if self.should_retry():
            self.state = 'failed'
            delay_seconds = self.calculate_retry_delay(backoff_base)
            self.next_retry_at = (
                datetime.utcnow() + timedelta(seconds=delay_seconds)
            ).isoformat()
        else:
            self.state = 'dead'
            self.next_retry_at = None
    
    def mark_processing(self):
        """Mark job as being processed"""
        self.state = 'processing'
        self.started_at = datetime.utcnow().isoformat()
        self.updated_at = self.started_at
    
    def mark_completed(self, output=None):
        """Mark job as completed"""
        self.state = 'completed'
        self.output = output
        self.completed_at = datetime.utcnow().isoformat()
        self.updated_at = self.completed_at
        
        # Calculate execution time
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            self.execution_time = (end - start).total_seconds()