from datetime import datetime
import os
from pathlib import Path
from .database import Database
from .job import Job

class QueueManager:
    """Manages job queue operations with bonus features"""
    
    def __init__(self, db_path="data/queuectl.db"):
        self.db = Database(db_path)
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def enqueue(self, job):
        """Add job to queue"""
        query = '''
            INSERT INTO jobs (id, command, state, attempts, max_retries,
                            created_at, updated_at, next_retry_at, 
                            error_message, output, priority, timeout, run_at,
                            started_at, completed_at, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            job.id, job.command, job.state, job.attempts, 
            job.max_retries, job.created_at, job.updated_at,
            job.next_retry_at, job.error_message, job.output,
            job.priority, job.timeout, job.run_at,
            job.started_at, job.completed_at, job.execution_time
        )
        self.db.execute_query(query, params)
        return job
    
    def get_next_job(self):
        """Get next job with priority and scheduling support"""
        conn = self.db._get_connection()
        conn.execute('BEGIN IMMEDIATE')
        
        try:
            # Priority queue: higher priority first, then FIFO
            # Only get jobs that are ready to run (run_at <= now or NULL)
            query = '''
                SELECT * FROM jobs 
                WHERE state IN ('pending', 'failed')
                AND (next_retry_at IS NULL OR next_retry_at <= ?)
                AND (run_at IS NULL OR run_at <= ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            '''
            now = datetime.utcnow().isoformat()
            row = self.db.fetch_one(query, (now, now))
            
            if row:
                job = Job.from_db_row(row)
                job.mark_processing()
                self.update_job(job)
                conn.commit()
                return job
            
            conn.commit()
            return None
        except Exception as e:
            conn.rollback()
            raise e
    
    def update_job(self, job):
        """Update job in database"""
        query = '''
            UPDATE jobs 
            SET command=?, state=?, attempts=?, max_retries=?,
                updated_at=?, next_retry_at=?, error_message=?, output=?,
                priority=?, timeout=?, run_at=?,
                started_at=?, completed_at=?, execution_time=?
            WHERE id=?
        '''
        params = (
            job.command, job.state, job.attempts, job.max_retries,
            job.updated_at, job.next_retry_at, job.error_message,
            job.output, job.priority, job.timeout, job.run_at,
            job.started_at, job.completed_at, job.execution_time,
            job.id
        )
        self.db.execute_query(query, params)
    
    def save_job_output(self, job_id, stdout, stderr):
        """Save job output to log file"""
        log_file = self.log_dir / f"{job_id}.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Job Output Log ===\n")
            f.write(f"Job ID: {job_id}\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n\n")
            f.write(f"--- STDOUT ---\n{stdout}\n\n")
            f.write(f"--- STDERR ---\n{stderr}\n")
    
    def get_job(self, job_id):
        """Get specific job by ID"""
        row = self.db.fetch_one('SELECT * FROM jobs WHERE id=?', (job_id,))
        return Job.from_db_row(row) if row else None
    
    def list_jobs(self, state=None, priority=None):
        """List jobs with optional filters"""
        if state and priority is not None:
            rows = self.db.fetch_all(
                'SELECT * FROM jobs WHERE state=? AND priority=? ORDER BY priority DESC, created_at DESC',
                (state, priority)
            )
        elif state:
            rows = self.db.fetch_all(
                'SELECT * FROM jobs WHERE state=? ORDER BY priority DESC, created_at DESC',
                (state,)
            )
        elif priority is not None:
            rows = self.db.fetch_all(
                'SELECT * FROM jobs WHERE priority=? ORDER BY created_at DESC',
                (priority,)
            )
        else:
            rows = self.db.fetch_all(
                'SELECT * FROM jobs ORDER BY priority DESC, created_at DESC'
            )
        return [Job.from_db_row(row) for row in rows]
    
    def get_stats(self):
        """Get queue statistics"""
        stats = {}
        for state in Job.STATES:
            row = self.db.fetch_one(
                'SELECT COUNT(*) as count FROM jobs WHERE state=?',
                (state,)
            )
            stats[state] = row['count'] if row else 0
        return stats
    
    def get_metrics(self):
        """Get execution metrics"""
        metrics = {}
        
        # Average execution time
        row = self.db.fetch_one(
            'SELECT AVG(execution_time) as avg_time FROM jobs WHERE execution_time IS NOT NULL'
        )
        metrics['avg_execution_time'] = row['avg_time'] if row and row['avg_time'] else 0
        
        # Success rate
        total = self.db.fetch_one('SELECT COUNT(*) as count FROM jobs')['count']
        completed = self.db.fetch_one('SELECT COUNT(*) as count FROM jobs WHERE state="completed"')['count']
        metrics['success_rate'] = (completed / total * 100) if total > 0 else 0
        
        # Jobs per hour (last 24 hours)
        row = self.db.fetch_one('''
            SELECT COUNT(*) as count FROM jobs 
            WHERE datetime(created_at) > datetime('now', '-1 day')
        ''')
        metrics['jobs_last_24h'] = row['count'] if row else 0
        
        # Priority distribution
        rows = self.db.fetch_all('''
            SELECT priority, COUNT(*) as count FROM jobs 
            GROUP BY priority ORDER BY priority DESC
        ''')
        metrics['priority_dist'] = {row['priority']: row['count'] for row in rows}
        
        return metrics
    
    def list_dlq(self):
        """List dead letter queue jobs"""
        return self.list_jobs(state='dead')
    
    def retry_dlq_job(self, job_id):
        """Retry a job from DLQ"""
        job = self.get_job(job_id)
        if not job or job.state != 'dead':
            return False
        
        job.state = 'pending'
        job.attempts = 0
        job.next_retry_at = None
        job.error_message = None
        job.updated_at = datetime.utcnow().isoformat()
        
        self.update_job(job)
        return True