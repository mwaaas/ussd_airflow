# To shorted build time
# build from the previously build image
# This will reduce the time needed to create
# installing al packages
# to build image from scratch  use this base image FROM python:3.5
FROM mwaaas/django_ussd_airflow:latest

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["/bin/bash", "./run.sh"]
