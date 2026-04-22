from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from model_utils import EmotionDetector, get_recommendations
import uvicorn
import io

app = FastAPI(title="Music Mood Classification API")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = EmotionDetector()

@app.get("/")
async def root():
    return {"message": "Music Mood API is running"}

@app.post("/predict")
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

@app.get("/genres")
async def get_genres():
    # List of supported genres for the UI
    return ["Punjabi", "Hindi", "English", "Rap", "Pop", "Old_90s"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
