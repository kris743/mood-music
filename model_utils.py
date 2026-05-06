import cv2
import numpy as np
import torch
from transformers import pipeline
import json
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

class EmotionDetector:
    # Map model output labels → app emotion keys used in songs.json
    LABEL_MAP = {
        'angry':    'angry',
        'disgust':  'disgust',
        'fear':     'fear',
        'happy':    'happy',
        'sad':      'sad',
        'surprise': 'surprise',
        'neutral':  'neutral',
    }

    def __init__(self):
        # Initialize OpenCV Face Detection (Haar Cascades)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Initialize Emotion Classification Pipeline
        # Using trpakov/vit-face-expression — a ViT fine-tuned on FER2013
        # with ~71% accuracy and much less neutral-bias than dima806's model
        print("Loading Emotion Classification Model (ViT)...")
        self.classifier = pipeline(
            "image-classification",
            model="trpakov/vit-face-expression",
            top_k=7,  # return all 7 emotion scores
        )
        print("Model Loaded.")

    def detect_emotion(self, image_bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, "Invalid Image Data"

        # Downscale large images for faster face detection
        h_orig, w_orig = img.shape[:2]
        max_dim = 640
        if max(h_orig, w_orig) > max_dim:
            scale = max_dim / max(h_orig, w_orig)
            img = cv2.resize(img, None, fx=scale, fy=scale)

        # Apply CLAHE contrast enhancement for better feature visibility
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        lab = cv2.merge([l_channel, a_channel, b_channel])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Convert to Gray for OpenCV detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None, "No face detected"

        # Extract the largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        
        # ── Expand the crop by 40% on each side ──
        # The Haar cascade bounding box is very tight and cuts off
        # eyebrows, forehead, and jawline — features critical for
        # emotion classification. Padding restores context the ViT
        # model was trained on.
        pad_w = int(w * 0.4)
        pad_h = int(h * 0.4)
        img_h, img_w = img.shape[:2]
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(img_w, x + w + pad_w)
        y2 = min(img_h, y + h + pad_h)
        
        # Convert to RGB for the transformer pipeline
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_img = img_rgb[y1:y2, x1:x2]
        
        # Resize face crop to model's expected size (224x224) for faster inference
        pil_img = Image.fromarray(face_img).resize((224, 224), Image.LANCZOS)
        
        # Run inference
        outputs = self.classifier(pil_img)
        
        # Debug: log top-3 predictions to diagnose bias
        print(f"[Emotion] Top-3: {[(o['label'], round(o['score'], 3)) for o in outputs[:3]]}")
        
        # The model returns a list of classes and scores. We take the top one.
        top_prediction = outputs[0]
        raw_label = top_prediction['label'].lower()
        mapped_label = self.LABEL_MAP.get(raw_label, 'neutral')
        return mapped_label, top_prediction['score']

from youtube_search import YoutubeSearch

# Search Cache: Avoid repeating expensive searches during a session
SEARCH_CACHE = {}

def _search_youtube_single(song):
    """Search YouTube for a single song. Called in parallel by ThreadPoolExecutor."""
    name = song['name']
    artist = song['artist']
    cache_key = f"{name}-{artist}".lower()

    if cache_key in SEARCH_CACHE:
        song['url'] = SEARCH_CACHE[cache_key]
        return song

    query = f"{name} {artist} official music video"
    print(f"Searching YouTube for: {query}")
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if results:
            video_id = results[0]['id']
            song_url = f"https://www.youtube.com/watch?v={video_id}"
            song['url'] = song_url
            SEARCH_CACHE[cache_key] = song_url
    except Exception as search_err:
        print(f"Search failed for {name}: {search_err}")

    return song

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

        # Try YouTube search — but don't let it kill the whole response
        try:
            with ThreadPoolExecutor(max_workers=5) as executor:
                final_songs = list(executor.map(_search_youtube_single, subset, timeout=10))
        except Exception as yt_err:
            print(f"YouTube search failed (non-fatal): {yt_err}")
            # Add fallback YouTube search URLs so the frontend can still work
            for song in subset:
                if 'url' not in song:
                    query = f"{song['name']} {song['artist']}".replace(' ', '+')
                    song['url'] = f"https://www.youtube.com/results?search_query={query}"
            final_songs = subset

        return {
            "emotion": mapped_emotion,
            "raw_emotion": emotion,
            "emoji": emotion_data.get('emoji', '🎵'),
            "songs": final_songs
        }
    except Exception as e:
        print(f"Error in recommendation logic: {e}")
        return {
            "emotion": emotion,
            "raw_emotion": emotion,
            "emoji": "🎵",
            "songs": []
        }

