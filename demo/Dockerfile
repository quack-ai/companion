FROM python:3.11-alpine3.19

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# copy requirements file
COPY demo/requirements.txt /app/requirements.txt

# install dependencies
RUN set -eux \
    && pip install --no-cache-dir uv \
    && uv pip install --no-cache --system -r /app/requirements.txt \
    && rm -rf /root/.cache

# copy project
COPY demo/assets /app/assets
COPY demo/styles /app/styles
COPY demo/main.py /app/main.py
