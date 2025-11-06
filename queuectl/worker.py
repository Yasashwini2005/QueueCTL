import subprocess
import time
import signal
from datetime import datetime
from .queue_manager import QueueManager
from .config import Config

class Worker:
    """Background worker with timeout and logging support"""
    
    def __init__(self, worker_id, db_path="data/queuectl.db"):
        self.worker_id = worker_id
        self.queue = QueueManager(db_path)
        self.config = Config(db_path)
        self.running = True
        self.current_job = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[Worker {self.worker_id}] Shutting down gracefully...")
        self.running = False
    
    def execute_command(self, command, timeout=300):
        """Execute shell command with configurable timeout"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Command timed out after {timeout} seconds',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
    
    def process_job(self, job):
        """Process a single job with metrics tracking"""
        print(f"[Worker {self.worker_id}] Processing job {job.id[:8]}: {job.command} (priority: {job.priority})")
        
        start_time = time.time()
        result = self.execute_command(job.command, timeout=job.timeout)
        execution_time = time.time() - start_time
        
        # Save output to log file
        self.queue.save_job_output(job.id, result['output'], result['error'])
        
        if result['success']:
            job.mark_completed(output=result['output'][:500])  # Store first 500 chars
            job.execution_time = execution_time
            print(f"[Worker {self.worker_id}] ✓ Job {job.id[:8]} completed in {execution_time:.2f}s")
        else:
            error_msg = result['error'] or f"Exit code: {result['return_code']}"
            backoff_base = int(self.config.get('backoff_base', 2))
            job.mark_for_retry(error_msg, backoff_base)
            
            if job.state == 'dead':
                print(f"[Worker {self.worker_id}] ✗ Job {job.id[:8]} moved to DLQ")
            else:
                delay = job.calculate_retry_delay(backoff_base)
                print(f"[Worker {self.worker_id}] ⟳ Job {job.id[:8]} will retry in {delay}s")
        
        self.queue.update_job(job)
    
    def run(self):
        """Main worker loop"""
        print(f"[Worker {self.worker_id}] Started")
        
        while self.running:
            try:
                job = self.queue.get_next_job()
                
                if job:
                    self.current_job = job
                    self.process_job(job)
                    self.current_job = None
                else:
                    time.sleep(2)
            
            except Exception as e:
                print(f"[Worker {self.worker_id}] Error: {e}")
                time.sleep(5)
        
        print(f"[Worker {self.worker_id}] Stopped")