FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9-alpine3.14

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/app"

# copy requirements file
COPY requirements.txt /app/requirements.txt

# install dependencies
RUN set -eux \
    && apk add --no-cache curl \
    && pip install --no-cache-dir uv \
    && uv pip install --no-cache --system -r /app/requirements.txt \
    && rm -rf /root/.cache

# copy project
COPY src/alembic.ini /app/alembic.ini
COPY src/migrations /app/migrations
COPY src/app /app/app
