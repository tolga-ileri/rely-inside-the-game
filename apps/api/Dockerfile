# Build context: repository root (needs synthetic-data/).  docker build -f apps/api/Dockerfile .
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    RELY_MATCHES_DIR=/app/synthetic-data/matches AI_PROVIDER=none LOG_LEVEL=INFO
WORKDIR /app/apps/api
COPY apps/api/requirements.txt .
RUN pip install -r requirements.txt
COPY apps/api/rely_brain ./rely_brain
COPY apps/api/main.py ./main.py
COPY synthetic-data/matches /app/synthetic-data/matches
RUN useradd --create-home --uid 10001 rely && chown -R rely /app
USER rely
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
