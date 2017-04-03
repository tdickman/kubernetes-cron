FROM        python:3.6-slim

ENV         PYTHONPATH /app:$PYTHONPATH
ENV         PYTHONUNBUFFERED 0
COPY        requirements.txt /tmp
RUN         pip3 install -r /tmp/requirements.txt

COPY        . /app

ENTRYPOINT  ["python3", "/app/kubcron/app.py"]
