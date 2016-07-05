FROM python:3.5.2-onbuild

EXPOSE 80

CMD ["/bin/bash", "./run.sh"]
