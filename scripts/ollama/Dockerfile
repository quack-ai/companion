FROM python:3.11-alpine3.19

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# install dependencies
RUN set -eux \
    && pip install --no-cache-dir uv \
    && uv pip install --no-cache --system requests==2.31.0 tqdm==4.66.2 numpy==1.26.4 \
    && rm -rf /root/.cache

# copy script
COPY ./evaluate_latency.py /app/evaluate.py
