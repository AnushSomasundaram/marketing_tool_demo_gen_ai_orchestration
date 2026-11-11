FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage/uploads storage/generated storage/composed

# Cloud Run sets $PORT (usually 8080) and expects the container to listen on
# it; sqlite:///./campaign_studio.db is ephemeral per container instance, so
# migrations run fresh on every startup rather than once at build/deploy time.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
