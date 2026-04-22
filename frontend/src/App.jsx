import { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL || '';

const GENRE_OPTIONS = [
  { id: 'punjabi',  label: '🕺 Punjabi' },
  { id: 'hindi',   label: '🎸 Hindi'   },
  { id: 'english', label: '🚀 English' },
  { id: 'rap',     label: '🎤 Rap'     },
  { id: 'pop',     label: '✨ Pop'     },
  { id: 'old_90s', label: '📼 90s'     },
];

const EMOTION_DEMO = [
  { emoji: '😊', label: 'Happy',   id: 'happy'   },
  { emoji: '😔', label: 'Sad',     id: 'sad'     },
  { emoji: '😠', label: 'Angry',   id: 'angry'   },
  { emoji: '😌', label: 'Calm',    id: 'calm'    },
  { emoji: '😲', label: 'Surprise',id: 'surprise'},
  { emoji: '😨', label: 'Fear',    id: 'fear'    },
  { emoji: '🤢', label: 'Disgust', id: 'disgust' },
  { emoji: '😐', label: 'Neutral', id: 'neutral' },
];

function getEmbedUrl(url) {
  if (!url) return null;
  const match = url.match(/[?&]v=([^&]+)/);
  const id = match ? match[1] : url.split('/').pop();
  return id ? `https://www.youtube.com/embed/${id}?autoplay=1&mute=1` : null;
}

export default function App() {
  const webcamRef    = useRef(null);
  const [detectedMood,    setDetectedMood]    = useState(null);
  const [confidence,      setConfidence]      = useState(null);
  const [selectedGenre,   setSelectedGenre]   = useState('hindi');
  const [isDetecting,     setIsDetecting]     = useState(false);
  const [isRefreshing,    setIsRefreshing]    = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [currentSongIdx,  setCurrentSongIdx]  = useState(0);
  const [error,           setError]           = useState(null);

  // Apply mood class to body for glow effects
  useEffect(() => {
    document.body.className = detectedMood ? `mood-${detectedMood}` : '';
  }, [detectedMood]);

  const captureAndSend = useCallback(async (genreOverride) => {
    setError(null);
    setIsDetecting(true);
    try {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (!imageSrc) throw new Error('Could not access webcam.');
      const blob = await fetch(imageSrc).then(r => r.blob());
      const form = new FormData();
      form.append('file', blob, 'capture.jpg');
      form.append('genre', genreOverride || selectedGenre);

      const res = await axios.post(`${API_BASE}/api/predict`, form);
      if (res.data.success) {
        setDetectedMood(res.data.recommendations.emotion);
        setConfidence(res.data.confidence);
        setRecommendations(res.data.recommendations);
        setCurrentSongIdx(0);
      } else {
        throw new Error(res.data.error || 'Detection failed.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong.');
    } finally {
      setIsDetecting(false);
    }
  }, [selectedGenre]);

  const refreshMix = async () => {
    if (!recommendations) return;
    setIsRefreshing(true);
    try {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (!imageSrc) return;
      const blob = await fetch(imageSrc).then(r => r.blob());
      const form = new FormData();
      form.append('file', blob, 'capture.jpg');
      form.append('genre', selectedGenre);
      const res = await axios.post(`${API_BASE}/api/predict`, form);
      if (res.data.success) {
        setRecommendations(res.data.recommendations);
        setCurrentSongIdx(0);
      }
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const currentSong    = recommendations?.songs?.[currentSongIdx];
  const currentEmbed   = getEmbedUrl(currentSong?.url);
  const moodEmoji      = EMOTION_DEMO.find(e => e.id === detectedMood)?.emoji || '🎵';

  return (
    <div className="app-shell">
      {/* ── TOP BAR ── */}
      <div className="top-bar">
        <div className="logo-wrap">
          <div className="logo-icon">🎵</div>
          <div>
            <div className="logo-text">MoodTunes AI</div>
            <div className="logo-sub">Emotion-Based Music</div>
          </div>
        </div>
        <div className="status-pill">
          <div className="status-dot" />
          AI Engine Active
        </div>
      </div>

      {/* ── TITLE ── */}
      <div className="title-area">
        <div className="title-badge">✦ Deep Space Edition</div>
        <h1>Feel the Music</h1>
        <p>Your face reveals your mood. Our AI finds the perfect soundtrack.</p>
      </div>

      {/* ── EMOTION CHIPS (decorative) ── */}
      <div className="emotion-demo-row" style={{ justifyContent: 'center', marginBottom: '32px' }}>
        {EMOTION_DEMO.map(e => (
          <div key={e.id} className="emotion-chip">{e.emoji} {e.label}</div>
        ))}
      </div>

      {/* ── MAIN GRID ── */}
      <div className="app-content">

        {/* ── LEFT: CAMERA + GENRE + BUTTON ── */}
        <div className="glass-card">
          <div className="panel-title">
            <span className="panel-title-icon">📷</span>
            Visual Analysis Studio
          </div>

          <div className="webcam-wrapper">
            <div className="scan-bracket tl" />
            <div className="scan-bracket tr" />
            <div className="scan-bracket bl" />
            <div className="scan-bracket br" />
            <div className="scan-line" />
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={{ width: 1280, height: 720, facingMode: 'user' }}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            />
          </div>

          <div className="section-label">Select Genre Focus</div>
          <div className="genre-selector">
            {GENRE_OPTIONS.map(g => (
              <button
                key={g.id}
                className={`genre-btn ${selectedGenre === g.id ? 'active' : ''}`}
                onClick={() => setSelectedGenre(g.id)}
              >
                {g.label}
              </button>
            ))}
          </div>

          <button
            className="detect-btn"
            onClick={() => captureAndSend()}
            disabled={isDetecting}
          >
            {isDetecting ? (
              <><div className="spinner" /> Analyzing Expression…</>
            ) : (
              '⚡ Scan My Expression'
            )}
          </button>

          {error && <div className="error-box">⚠️ {error}</div>}
        </div>

        {/* ── RIGHT: PLAYER + SONGS ── */}
        <div className="glass-card">
          <div className="panel-title">
            <span className="panel-title-icon">🎧</span>
            Mood-Matched Stream
            {recommendations && (
              <button
                className="refresh-btn"
                onClick={refreshMix}
                disabled={isRefreshing}
                title="Shuffle new songs"
              >
                {isRefreshing ? '…' : '🔄'}
              </button>
            )}
          </div>

          {recommendations && currentSong ? (
            <>
              {/* MOOD INFO */}
              <div className="mood-result">
                <div className="mood-emoji-big">{moodEmoji}</div>
                <div>
                  <div className="mood-label">{detectedMood}</div>
                  <div className="mood-meta">
                    {confidence ? `${Math.round(confidence * 100)}% confidence` : ''} · {selectedGenre.toUpperCase()} Mix
                  </div>
                </div>
              </div>

              {/* YOUTUBE PLAYER */}
              <div className="player-container">
                <iframe
                  key={currentEmbed}
                  title="Music Player"
                  width="100%"
                  height="100%"
                  src={currentEmbed}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>

              <div className="muted-notice">
                🔇 Auto-muted by browser. Click speaker icon inside player to unmute!
              </div>

              {/* NOW PLAYING */}
              <div className="now-playing-info">
                <div className="playing-dot" />
                <div>
                  <div className="song-name">{currentSong.name}</div>
                  <div className="song-artist">{currentSong.artist} · {selectedGenre.toUpperCase()}</div>
                </div>
              </div>

              {/* MOOD CORRECTION */}
              <div className="mood-correction">
                <div className="correction-label">AI got it wrong? Adjust your mood:</div>
                <div className="correction-chips">
                  {EMOTION_DEMO.map(m => (
                    <button
                      key={m.id}
                      className={`correction-chip ${detectedMood === m.id ? 'active' : ''}`}
                      onClick={() => { setDetectedMood(m.id); captureAndSend(m.id); }}
                      title={m.label}
                    >
                      {m.emoji}
                    </button>
                  ))}
                </div>
              </div>

              {/* SONG LIST */}
              <div className="song-list-wrap">
                <div className="songs-section-label">Suggested Mix</div>
                <div className="song-list">
                  {recommendations.songs.map((song, idx) => (
                    <div
                      key={idx}
                      className={`song-list-item ${currentSongIdx === idx ? 'active' : ''}`}
                      onClick={() => setCurrentSongIdx(idx)}
                    >
                      <span className="song-num">{currentSongIdx === idx ? '▶' : idx + 1}</span>
                      <div className="song-list-info">
                        <div className="song-list-name">{song.name}</div>
                        <div className="song-list-artist">{song.artist}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">💿</div>
              <h3>Ready for Detection</h3>
              <p>Choose a genre, look at the camera, and let the AI find your vibe.</p>
            </div>
          )}
        </div>
      </div>

      <footer className="app-footer">
        © 2026 MoodTunes AI · Powered by Vision Transformers · Deep Space Edition
      </footer>
    </div>
  );
}
