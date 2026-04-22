# 🛰️ NetPulse — WiFi Experience Intelligence Platform

> A cross-platform network analyzer that transforms technical metrics into human-readable stories and generative art.

---

## 🚀 Features

- **🔥 WiFi Story Mode**: AI-powered narration of your connection history.
- **🔥 Living Signal Map**: Generative waveform art reflecting real-time signal health.
- **🔥 QoE Application Profiler**: Performance ratings for Zoom, Gaming, and Streaming.
- **🔥 Root Cause Engine**: Automatic detection of interference and congestion.

---

## 🛠️ Deployment Instructions

### 1. Backend (Render)
1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository.
3. Use the following settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app`
4. Add **Environment Variables**:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `PORT`: 10000 (default)

### 2. Frontend (Netlify)
1. Create a new site on [Netlify](https://netlify.com).
2. Select the `frontend/` directory as the **Base directory**.
3. Set **Publish directory** to `.`.
4. **IMPORTANT**: Update the `API_BASE_URL` in `frontend/index.html` to point to your Render backend URL.

---

## 🛠️ Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the platform:
   ```bash
   python netpulse.py
   ```
3. Open `frontend/index.html` in your browser.

---

## 📊 Feature Comparison

| Feature | Basic Ping | NetPulse |
|---|---|---|
| Latency Monitoring | ✅ | ✅ |
| Jitter/Packet Loss | ❌ | ✅ |
| Living Signal Map | ❌ | ✅ (Generative Art) |
| WiFi Story Mode | ❌ | ✅ (AI Narration) |
| "What If" Simulator | ❌ | ✅ (Predictive QoE) |
| Root Cause Detection | ❌ | ✅ (Automatic) |

---

## 🏗️ Project Structure

- `agent/`: Network metric collectors (Windows & Linux).
- `api/`: FastAPI backend and SSE stream.
- `frontend/`: React-based dashboard with Tailwind and Framer Motion.
- `normalizer.py`: Metrics windowing and normalization.
- `analyzer.py`: Root cause detection logic.
- `qoe.py`: Quality of Experience scoring engine.

---

## 👥 Authors
Team Cognita
