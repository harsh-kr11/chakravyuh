# CHAKRAVYUH API image
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install ".[api,detect]"

# Non-root user
RUN useradd -m -u 10001 chakra && chown -R chakra:chakra /app
USER chakra

EXPOSE 8080
ENV CHAKRAVYUH_API_HOST=0.0.0.0 CHAKRAVYUH_API_PORT=8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status==200 else 1)"

CMD ["uvicorn", "chakravyuh.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
