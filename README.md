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
