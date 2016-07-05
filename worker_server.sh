#!/usr/bin/env bash


celery -A django_ussd_airflow worker -E -n ussd-worker \
--concurrency=3 \
--loglevel=info
