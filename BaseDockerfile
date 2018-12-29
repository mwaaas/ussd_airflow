FROM python:3.5

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /tmp/
COPY default.txt /tmp/

RUN pip install --no-cache-dir --exists-action w -r /tmp/requirements.txt

ONBUILD COPY . /usr/src/app
ONBUILD RUN pip install --no-cache-dir --exists-action w -r requirements.txt

EXPOSE 80

CMD ["/bin/bash", "./run.sh"]
