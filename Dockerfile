# Multi-stage Dockerfile for NeuroSentry Clinical Console.
# Stage 1: build the React frontend to static assets.
# Stage 2: install Python + torch, copy backend + built frontend, run uvicorn.

# -------- Stage 1: frontend build --------
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Install deps first (better layer cache)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

# Build
COPY frontend/ ./
RUN npm run build

# -------- Stage 2: backend runtime --------
FROM python:3.11-slim AS runtime

# System deps for scipy / torch
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps with CPU-only torch to keep image small
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source + shipped pretrained checkpoint + shipped patient recordings
COPY backend/app ./backend/app
COPY backend/checkpoints ./backend/checkpoints
COPY backend/data ./backend/data
# Copy built frontend into the expected location
COPY --from=frontend-builder /build/dist ./frontend/dist

# Ensure the dirs exist even if a user mounts an empty volume
RUN mkdir -p /app/backend/data /app/backend/checkpoints

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    NEUROSENTRY_HOST=0.0.0.0

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -fsS http://localhost:${PORT:-8000}/api/health || exit 1

# ${PORT} is used by Railway / Render; falls back to 8000 locally
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
