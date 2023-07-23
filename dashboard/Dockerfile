FROM python:3.9-slim

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# copy requirements file
COPY requirements.txt /app/requirements.txt

# install dependencies
RUN pip install --upgrade --no-cache-dir pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip cache purge \
    && rm -rf /root/.cache/pip

# copy project
COPY app.py /app/app.py
