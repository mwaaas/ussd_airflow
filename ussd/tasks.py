from celery import current_app as app
import requests

@app.task(bind=True)
def http_task(self, request_conf):
    requests.request(**request_conf)