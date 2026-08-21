FROM python:3.13-slim

WORKDIR /app

# System deps: libpq for asyncpg build (uses pure C extension, needs no libpq
# at runtime, but psycopg-style native deps commonly need build-essential —
# kept minimal since asyncpg ships wheels for this platform).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
