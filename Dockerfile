# Builder stage
FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    git \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

COPY . /usr/src/app
WORKDIR /usr/src/app

RUN uv sync

# Production stage
FROM python:3.13-slim-bookworm

COPY --from=builder /usr/src/app/.venv/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/src/app /usr/src/app
COPY --from=builder /usr/src/app/.venv/bin/uwsgi /usr/local/bin/
WORKDIR /usr/src/app

RUN python manage.py collectstatic --no-input
