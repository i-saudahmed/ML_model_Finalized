"""
Gunicorn configuration for ML Model API
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5001)}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'ml_model_api'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application
preload_app = True

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("ML Model API server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """Called just after a worker has been killed by a signal."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
