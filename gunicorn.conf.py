# ==============================================================
# Gunicorn Configuration File - Irrigación Malargüe
# ==============================================================
# Production-ready configuration for Docker + Cloudflare Tunnel
# ==============================================================

import multiprocessing
import os

# Server Socket
# Bind to 0.0.0.0:8000 inside container (mapped to 8002 externally)
bind = "0.0.0.0:8000"
backlog = 2048

# Worker Processes
# Formula: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000

# Request handling
max_requests = 1000  # Restart worker after 1000 requests (memory leak protection)
max_requests_jitter = 100  # Random jitter to avoid thundering herd
timeout = 60  # Worker timeout (60s)
keepalive = 5  # Keep-alive connections

# Logging
accesslog = "/var/log/malargue/gunicorn_access.log"
errorlog = "/var/log/malargue/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "irrigacion_malargue"

# Server Mechanics
daemon = False  # Run in foreground (Docker manages the process)
pidfile = None  # No PID file needed in Docker
user = None  # User set in Dockerfile
group = None  # Group set in Dockerfile
umask = 0o007

# Security
# SSL is handled by Cloudflare Tunnel, so no need for keyfile/certfile here
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Environment
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings",
]

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 Irrigación Malargüe starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("♻️  Reloading Irrigación Malargüe...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ Irrigación Malargüe ready to serve requests on %s", bind)

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("🛑 Irrigación Malargüe shutting down...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("🔄 Worker %s received INT or QUIT signal", worker.pid)

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.error("⚠️  Worker %s received SIGABRT signal", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Forking worker %s", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker %s spawned", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info("Worker %s exited", worker.pid)
