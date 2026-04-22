import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from model_utils import EmotionDetector, get_recommendations
import uvicorn

app = FastAPI(title="Music Mood Classification API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = EmotionDetector()

@app.get("/api/health")
async def root():
    return {"message": "Music Mood API is running"}

@app.post("/api/predict")
async def predict_mood(file: UploadFile = File(...), genre: str = Form("hindi")):
    try:
        contents = await file.read()
        emotion, confidence = detector.detect_emotion(contents)

        if emotion is None:
            return {"error": confidence}

        results = get_recommendations(emotion, genre)

        return {
            "success": True,
            "detected_emotion": emotion,
            "confidence": float(confidence),
            "recommendations": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/genres")
async def get_genres():
    return ["Punjabi", "Hindi", "English", "Rap", "Pop", "Old_90s"]

# ── Serve React frontend static files ──────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve API paths normally — only catch non-api routes for SPA
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
