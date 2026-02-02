# ==============================================================
# Gunicorn Configuration File
# ==============================================================
# Uso: gunicorn -c gunicorn.conf.py config.wsgi:application
# ==============================================================

import multiprocessing
import os

# Server Socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5

# Logging
accesslog = "/var/log/malargue/gunicorn_access.log"
errorlog = "/var/log/malargue/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "malargue_gunicorn"

# Server Mechanics
daemon = False
pidfile = "/var/run/gunicorn/malargue.pid"
user = "malargue"
group = "www-data"
umask = 0o007

# SSL (si lo necesitás directamente en Gunicorn, generalmente va en Nginx)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

# Environment
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings",
]

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Malargüe DB starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Malargüe DB...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Malargüe DB ready to serve requests")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Malargüe DB shutting down...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
