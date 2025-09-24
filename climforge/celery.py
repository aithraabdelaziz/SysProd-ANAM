import os
from celery import Celery

# Configure le module Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'climforge.settings.dev')

app = Celery('climforge')

# Charge la configuration depuis les settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-détecte les tâches
app.autodiscover_tasks()
