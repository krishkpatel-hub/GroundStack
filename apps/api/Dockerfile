FROM python:3.14.2-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system groundstack && adduser --system --ingroup groundstack groundstack

COPY apps/api/pyproject.toml /app/
COPY apps/api/app /app/app
COPY apps/api/migrations /app/migrations
COPY apps/api/alembic.ini /app/alembic.ini

RUN pip install --upgrade pip \
    && pip install .

USER groundstack

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/api/v1/health/live', timeout=3).read()"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
