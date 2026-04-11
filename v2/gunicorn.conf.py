import os

bind = "0.0.0.0:" + str(os.environ.get("PORT", "5000"))
workers = 4
threads = 4
timeout = 120
worker_class = "gthread"
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
loglevel = "info"