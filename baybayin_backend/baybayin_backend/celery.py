import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baybayin_backend.settings')

app = Celery('baybayin_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()