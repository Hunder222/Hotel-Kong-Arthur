# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- Runtime Stage ---
FROM base AS runtime

COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install .

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "hotel_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Test Stage ---
FROM runtime AS test

RUN pip install .[dev]

COPY tests/ ./tests/

CMD ["pytest"]

