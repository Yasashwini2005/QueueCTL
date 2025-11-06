import click
import json
import multiprocessing
import os
import signal
from tabulate import tabulate
from colorama import init, Fore, Style
from pathlib import Path

from .queue_manager import QueueManager
from .job import Job
from .worker import Worker
from .config import Config

init()

DB_PATH = "data/queuectl.db"
WORKER_PIDS_FILE = "data/workers.pid"


# ============= MAIN CLI GROUP =============
@click.group()
def cli():
    """QueueCTL - Background Job Queue System"""
    pass


# ============= ENQUEUE COMMAND =============
@cli.command()
@click.argument('job_data', required=False)
@click.option('--command', '-c', help='Command to execute')
@click.option('--id', 'job_id', help='Job ID (optional)')
@click.option('--max-retries', '-r', default=None, type=int, help='Max retries')
@click.option('--priority', '-p', default=0, type=int, help='Priority (higher = more important)')
@click.option('--timeout', '-t', default=300, type=int, help='Timeout in seconds')
@click.option('--run-at', help='Schedule job (ISO format: 2025-11-05T15:30:00)')
def enqueue(job_data, command, job_id, max_retries, priority, timeout, run_at):
    """Enqueue a new job with bonus features
    
    Examples:
    
    \b
    Basic:
      queuectl enqueue --command "echo Hello"
    
    \b
    High priority:
      queuectl enqueue -c "important_task.py" -p 10
    
    \b
    With timeout:
      queuectl enqueue -c "long_process.sh" -t 600
    
    \b
    Scheduled:
      queuectl enqueue -c "backup.sh" --run-at "2025-11-05T15:30:00"
    """
    try:
        if job_data:
            try:
                data = json.loads(job_data)
            except json.JSONDecodeError:
                click.echo(f"{Fore.RED}Error: Invalid JSON{Style.RESET_ALL}")
                return
        elif command:
            data = {'command': command}
            if job_id:
                data['id'] = job_id
            if max_retries is not None:
                data['max_retries'] = max_retries
            if priority != 0:
                data['priority'] = priority
            if timeout != 300:
                data['timeout'] = timeout
            if run_at:
                data['run_at'] = run_at
        else:
            click.echo(f"{Fore.RED}Error: Must provide --command or JSON{Style.RESET_ALL}")
            return
        
        if 'command' not in data:
            click.echo(f"{Fore.RED}Error: 'command' required{Style.RESET_ALL}")
            return
        
        config = Config(DB_PATH)
        if 'max_retries' not in data:
            data['max_retries'] = int(config.get('max_retries', 3))
        
        job = Job.from_dict(data)
        queue = QueueManager(DB_PATH)
        queue.enqueue(job)
        
        click.echo(f"{Fore.GREEN}✓ Job enqueued{Style.RESET_ALL}")
        click.echo(f"  ID: {job.id}")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  Priority: {job.priority}")
        click.echo(f"  Timeout: {job.timeout}s")
        if job.run_at:
            click.echo(f"  Scheduled for: {job.run_at}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


# ============= WORKER COMMANDS =============
@cli.group()
def worker():
    """Manage workers"""
    pass


def worker_process(worker_id):
    """Worker process function"""
    w = Worker(worker_id, DB_PATH)
    w.run()


@worker.command()
@click.option('--count', default=1, help='Number of workers to start')
def start(count):
    """Start worker processes"""
    click.echo(f"Starting {count} worker(s)...")
    
    processes = []
    for i in range(count):
        p = multiprocessing.Process(target=worker_process, args=(f"W{i+1}",))
        p.start()
        processes.append(p)
        click.echo(f"{Fore.GREEN}✓ Worker W{i+1} started (PID: {p.pid}){Style.RESET_ALL}")
    
    # Save PIDs
    os.makedirs(os.path.dirname(WORKER_PIDS_FILE), exist_ok=True)
    with open(WORKER_PIDS_FILE, 'w') as f:
        for p in processes:
            f.write(f"{p.pid}\n")
    
    click.echo(f"\n{Fore.CYAN}Workers running. Press Ctrl+C to stop.{Style.RESET_ALL}")
    
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}Stopping workers gracefully...{Style.RESET_ALL}")
        for p in processes:
            p.terminate()
            p.join()
        click.echo(f"{Fore.GREEN}All workers stopped{Style.RESET_ALL}")


@worker.command()
def stop():
    """Stop all running workers"""
    if not os.path.exists(WORKER_PIDS_FILE):
        click.echo(f"{Fore.YELLOW}No workers PID file found{Style.RESET_ALL}")
        return
    
    with open(WORKER_PIDS_FILE, 'r') as f:
        pids = [int(line.strip()) for line in f if line.strip()]
    
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            click.echo(f"{Fore.GREEN}✓ Sent stop signal to worker (PID: {pid}){Style.RESET_ALL}")
        except ProcessLookupError:
            click.echo(f"{Fore.YELLOW}Worker (PID: {pid}) not found{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}Error stopping worker (PID: {pid}): {e}{Style.RESET_ALL}")
    
    os.remove(WORKER_PIDS_FILE)


# ============= STATUS COMMAND =============
@cli.command()
def status():
    """Show queue status and statistics"""
    queue = QueueManager(DB_PATH)
    stats = queue.get_stats()
    
    click.echo(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}QueueCTL Status{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    table_data = []
    colors = {
        'pending': Fore.YELLOW,
        'processing': Fore.BLUE,
        'completed': Fore.GREEN,
        'failed': Fore.MAGENTA,
        'dead': Fore.RED
    }
    
    for state in Job.STATES:
        count = stats.get(state, 0)
        color = colors.get(state, '')
        table_data.append([
            f"{color}{state.upper()}{Style.RESET_ALL}",
            f"{color}{count}{Style.RESET_ALL}"
        ])
    
    click.echo(tabulate(table_data, headers=['State', 'Count'], tablefmt='grid'))
    click.echo()


# ============= LIST COMMAND =============
@cli.command()
@click.option('--state', help='Filter by state')
@click.option('--limit', default=20, help='Maximum number of jobs to display')
def list(state, limit):
    """List jobs"""
    queue = QueueManager(DB_PATH)
    jobs = queue.list_jobs(state=state)[:limit]
    
    if not jobs:
        click.echo(f"{Fore.YELLOW}No jobs found{Style.RESET_ALL}")
        return
    
    table_data = []
    for job in jobs:
        # Get priority, default to 0 if not set
        priority = getattr(job, 'priority', 0)
        
        table_data.append([
            job.id[:8] + '...',
            job.command[:30] + ('...' if len(job.command) > 30 else ''),
            job.state,
            f"{job.attempts}/{job.max_retries}",
            f"P{priority}",
            job.created_at[:19]
        ])
    
    click.echo(tabulate(
        table_data,
        headers=['ID', 'Command', 'State', 'Attempts', 'Priority', 'Created At'],
        tablefmt='grid'
    ))


# ============= DLQ COMMANDS =============
@cli.group()
def dlq():
    """Dead Letter Queue operations"""
    pass


@dlq.command('list')
def dlq_list():
    """List jobs in DLQ"""
    queue = QueueManager(DB_PATH)
    jobs = queue.list_dlq()
    
    if not jobs:
        click.echo(f"{Fore.GREEN}DLQ is empty{Style.RESET_ALL}")
        return
    
    table_data = []
    for job in jobs:
        table_data.append([
            job.id[:8] + '...',
            job.command[:30],
            job.attempts,
            (job.error_message[:40] + '...') if job.error_message and len(job.error_message) > 40 else job.error_message
        ])
    
    click.echo(tabulate(
        table_data,
        headers=['ID', 'Command', 'Attempts', 'Last Error'],
        tablefmt='grid'
    ))


@dlq.command('retry')
@click.argument('job_id')
def dlq_retry(job_id):
    """Retry a job from DLQ"""
    queue = QueueManager(DB_PATH)
    
    if queue.retry_dlq_job(job_id):
        click.echo(f"{Fore.GREEN}✓ Job {job_id} moved back to pending queue{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.RED}✗ Job {job_id} not found in DLQ{Style.RESET_ALL}")


# ============= CONFIG COMMANDS =============
@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set configuration value
    
    Available keys: max-retries, backoff-base
    """
    key_map = {
        'max-retries': 'max_retries',
        'backoff-base': 'backoff_base'
    }
    
    actual_key = key_map.get(key, key)
    cfg = Config(DB_PATH)
    cfg.set(actual_key, value)
    click.echo(f"{Fore.GREEN}✓ Configuration updated: {key} = {value}{Style.RESET_ALL}")


@config.command('get')
@click.argument('key', required=False)
def config_get(key):
    """Get configuration value(s)"""
    cfg = Config(DB_PATH)
    
    if key:
        key_map = {
            'max-retries': 'max_retries',
            'backoff-base': 'backoff_base'
        }
        actual_key = key_map.get(key, key)
        value = cfg.get(actual_key)
        click.echo(f"{key}: {value}")
    else:
        all_config = cfg.get_all()
        table_data = [[k, v] for k, v in all_config.items()]
        click.echo(tabulate(table_data, headers=['Key', 'Value'], tablefmt='grid'))


# ============= METRICS COMMAND =============
@cli.command()
def metrics():
    """Show execution metrics and statistics"""
    queue = QueueManager(DB_PATH)
    stats = queue.get_stats()
    metrics = queue.get_metrics()
    
    click.echo(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}QueueCTL Metrics & Statistics{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Job counts
    click.echo(f"{Fore.YELLOW}Job Counts:{Style.RESET_ALL}")
    table_data = [[state.upper(), count] for state, count in stats.items()]
    click.echo(tabulate(table_data, headers=['State', 'Count'], tablefmt='grid'))
    
    # Performance metrics
    click.echo(f"\n{Fore.YELLOW}Performance Metrics:{Style.RESET_ALL}")
    perf_data = [
        ['Average Execution Time', f"{metrics['avg_execution_time']:.2f}s"],
        ['Success Rate', f"{metrics['success_rate']:.1f}%"],
        ['Jobs (Last 24h)', metrics['jobs_last_24h']]
    ]
    click.echo(tabulate(perf_data, headers=['Metric', 'Value'], tablefmt='grid'))
    
    # Priority distribution
    if metrics['priority_dist']:
        click.echo(f"\n{Fore.YELLOW}Priority Distribution:{Style.RESET_ALL}")
        prio_data = [[prio, count] for prio, count in metrics['priority_dist'].items()]
        click.echo(tabulate(prio_data, headers=['Priority', 'Jobs'], tablefmt='grid'))
    
    click.echo()


# ============= LOGS COMMAND =============
@cli.command()
@click.argument('job_id')
def logs(job_id):
    """View job output logs"""
    log_file = Path(f"data/logs/{job_id}.log")
    
    if not log_file.exists():
        click.echo(f"{Fore.YELLOW}No log file found for job {job_id}{Style.RESET_ALL}")
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    click.echo(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    click.echo(content)
    click.echo(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


# ============= DASHBOARD COMMAND =============
@cli.command()
@click.option('--port', default=5000, help='Port to run dashboard')
@click.option('--host', default='127.0.0.1', help='Host to bind')
def dashboard(port, host):
    """Start web dashboard for monitoring"""
    click.echo(f"{Fore.CYAN}Starting QueueCTL Dashboard...{Style.RESET_ALL}")
    click.echo(f"Dashboard running at: {Fore.GREEN}http://{host}:{port}{Style.RESET_ALL}")
    click.echo(f"Press {Fore.YELLOW}Ctrl+C{Style.RESET_ALL} to stop\n")
    
    from .dashboard import run_dashboard
    run_dashboard(host=host, port=port)


# ============= MAIN ENTRY POINT =============
def main():
    cli()


if __name__ == '__main__':
    main()
