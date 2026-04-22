---
title: MoodTunes AI
emoji: 🎵
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: Detect your mood from your face and get music recommendations
---

# MoodTunes AI 🎵

**Emotion-Based Music Recommendation powered by Computer Vision**

Upload or capture a photo → AI detects your facial emotion → Get personalized music recommendations across multiple genres.

## Features
- 🤖 **Real-time emotion detection** using ViT (Vision Transformer) model
- 🎧 **6 Genre filters**: Punjabi, Hindi, English, Rap, Pop, 90s
- 🎬 **YouTube integration** with embedded player
- 😊 8 emotions: Happy, Sad, Angry, Calm, Surprise, Fear, Disgust, Neutral

## Tech Stack
- **Backend**: FastAPI + OpenCV + HuggingFace Transformers
- **Frontend**: React + Vite + TailwindCSS
- **Model**: `dima806/facial_emotions_image_detection`

## Local run

### Backend
```bash
python -m pip install -r requirements.txt
python app.py
```
Backend runs at `http://127.0.0.1:8000` and docs at `http://127.0.0.1:8000/docs`.

### Frontend (dev)
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

## Deploy (single-container Docker: backend + built frontend)

This repo includes a `Dockerfile` that:
- builds the Vite frontend
- serves it from the FastAPI backend

### Render (Docker)
1. Render → **New** → **Web Service**
2. Connect GitHub repo: `kris743/mood-music`
3. **Environment**: Docker
4. Deploy

Open your Render service URL to use the app UI.

## API endpoints
- `GET /api/health`
- `GET /api/genres`
- `POST /api/predict` (multipart form-data: `file`, `genre`)
- Legacy aliases (kept for compatibility): `GET /genres`, `POST /predict`
