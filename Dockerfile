# ────────────────────────────────────────────────────────────────────────────
# Stage 1 – Build the React frontend
# ────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ────────────────────────────────────────────────────────────────────────────
# Stage 2 – Python backend + copy frontend dist
# ────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System deps for OpenCV headless
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (CPU-only torch via extra index)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY app.py model_utils.py songs.json ./

# Copy built React app from stage 1
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

# HuggingFace Spaces expects port 7860
EXPOSE 7860
ENV PORT=7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
