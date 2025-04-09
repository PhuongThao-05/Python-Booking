import os
import threading
from django.apps import AppConfig

from booking import settings


class MyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"
    ngrok_started = False

    def ready(self):
        if os.getenv('RUN_MAIN') != 'true':
            return
        if not MyappConfig.ngrok_started:
            from .customer.customer_features import start_ngrok

            thread = threading.Thread(target=start_ngrok)
            thread.setDaemon(True)
            thread.start()

            MyappConfig.ngrok_started = True