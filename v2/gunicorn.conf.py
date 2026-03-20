# Konfiguracja serwera Gunicorn
workers = 4
bind = "0.0.0.0:5000"
wsgi_app = "app:app"

# (Opcjonalnie) logowanie dostosowane do kontenerów lub standardowego wyjścia
accesslog = "-"
errorlog = "-"