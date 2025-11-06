from flask import Flask, render_template, jsonify, request
from .queue_manager import QueueManager
from .config import Config
import os
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).parent

app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'))
queue = QueueManager()
config = Config()

@app.route('/')
def index():
    """Dashboard home page"""
    stats = queue.get_stats()
    metrics = queue.get_metrics()
    return render_template('dashboard.html', stats=stats, metrics=metrics)

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time stats"""
    return jsonify(queue.get_stats())

@app.route('/api/jobs')
def api_jobs():
    """API endpoint for job list"""
    state = request.args.get('state')
    jobs = queue.list_jobs(state=state)
    return jsonify([job.to_dict() for job in jobs[:50]])  # Limit to 50

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics"""
    return jsonify(queue.get_metrics())

def run_dashboard(host='127.0.0.1', port=5000):
    """Start the dashboard server"""
    print(f"Dashboard starting at http://{host}:{port}")
    print(f"Template folder: {app.template_folder}")
    app.run(host=host, port=port, debug=False)