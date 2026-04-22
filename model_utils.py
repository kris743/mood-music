import cv2
import numpy as np
import torch
from transformers import pipeline
import json
import os
from PIL import Image

class EmotionDetector:
    def __init__(self):
        # Initialize OpenCV Face Detection (Haar Cascades)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Initialize Emotion Classification Pipeline (ViT model)
        print("Loading Emotion Classification Model (ViT)...")
        self.classifier = pipeline("image-classification", model="dima806/facial_emotions_image_detection")
        print("Model Loaded.")

    def detect_emotion(self, image_bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, "Invalid Image Data"

        # Convert to Gray for OpenCV detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None, "No face detected"

        # Extract the first face
        (x, y, w, h) = faces[0]
        
        # Convert to RGB for the transformer pipeline
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_img = img_rgb[y:y+h, x:x+w]
        
        # Convert cropped face to PIL Image for the transformer pipeline
        pil_img = Image.fromarray(face_img)
        
        # Run inference
        outputs = self.classifier(pil_img)
        
        # The model returns a list of classes and scores. We take the top one.
        # Format: [{'label': 'happy', 'score': 0.9}, ...]
        top_prediction = outputs[0]
        return top_prediction['label'], top_prediction['score']

from youtube_search import YoutubeSearch

# Search Cache: Avoid repeating expensive searches during a session
SEARCH_CACHE = {}

def get_recommendations(emotion, genre="hindi"):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        songs_path = os.path.join(base_dir, 'songs.json')
        with open(songs_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        mapped_emotion = emotion.lower().strip()
        valid = set(data['emotions'].keys())
        if mapped_emotion not in valid:
            mapped_emotion = 'happy'

        emotion_data = data['emotions'][mapped_emotion]
        
        # Exact matching for the requested genre
        genre_key = genre.lower().strip()
        # Handle the special 'Old_90s' name from UI to JSON 'old_90s'
        if genre_key == 'old_90s':
            genre_key = 'old_90s'
        
        songs_pool = emotion_data.get(genre_key, [])

        # Fallback ONLY if the selected genre has no songs at all for this mood
        if not songs_pool:
            print(f"Warning: Genre {genre_key} empty for {mapped_emotion}. Falling back.")
            songs_pool = emotion_data.get('english', []) or emotion_data.get('hindi', [])
        
        # If still nothing, pick the first available genre list
        if not songs_pool:
            for g_key in emotion_data:
                if isinstance(emotion_data[g_key], list) and emotion_data[g_key]:
                    songs_pool = emotion_data[g_key]
                    break

        import random
        selected_songs = list(songs_pool)
        random.shuffle(selected_songs)
        subset = selected_songs[:5]

        # Enhance songs with dynamic YouTube links
        final_songs = []
        for s in subset:
            name = s['name']
            artist = s['artist']
            cache_key = f"{name}-{artist}".lower()
            
            if cache_key in SEARCH_CACHE:
                s['url'] = SEARCH_CACHE[cache_key]
            else:
                # Use dynamic search to get a fresh, working URL
                query = f"{name} {artist} official music video"
                print(f"Searching YouTube for: {query}")
                try:
                    results = YoutubeSearch(query, max_results=1).to_dict()
                    if results:
                        video_id = results[0]['id']
                        song_url = f"https://www.youtube.com/watch?v={video_id}"
                        s['url'] = song_url
                        SEARCH_CACHE[cache_key] = song_url
                    else:
                        # Keep original if search fails
                        pass
                except Exception as search_err:
                    print(f"Search failed for {name}: {search_err}")

            final_songs.append(s)

        return {
            "emotion": mapped_emotion,
            "raw_emotion": emotion,
            "emoji": emotion_data.get('emoji', '🎵'),
            "songs": final_songs
        }
    except Exception as e:
        print(f"Error in recommendation logic: {e}")
        return None
