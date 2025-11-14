# TODO: update maintainer and possibly python version
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /app/

RUN pip install --no-cache-dir poetry && \
    poetry install --no-root

COPY src /app/src
ENV PYTHONPATH=/app/src

EXPOSE 8000

# TODO: rename when changing entrypoint
CMD ["poetry", "run", "app"]
