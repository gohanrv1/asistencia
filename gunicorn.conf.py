"""
Configuración de Gunicorn para producción
"""

# Bind
bind = "0.0.0.0:8000"

# Workers
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "asistencia"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (deshabilitado - lo maneja el proxy)
keyfile = None
certfile = None

# Proxy settings
forwarded_allow_ips = "*"
proxy_protocol = False
proxy_allow_ips = "*"

# Preload app
preload_app = False
