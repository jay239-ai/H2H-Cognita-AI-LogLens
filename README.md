# 🛰️ NetPulse — WiFi Experience Intelligence Platform

> Real-time, browser-based network analyzer with live charts, speed tests, anomaly detection, and intelligent diagnostics. Fully hostable on Render + Netlify.

---

## 🚀 Features

### Core Intelligence
- **QoE Scoring Engine** — Weighted quality score (latency, jitter, loss, throughput) with animated gauge
- **Root Cause Analysis** — Automatic detection of interference, congestion, and signal issues with mitigations
- **WiFi Story Mode** — Rule-based narrative engine that explains what happened, why, and what to do
- **App Profiler** — Performance ratings for Video Calls, Gaming, Streaming, and Browsing
- **"What If" Simulator** — Predict network quality under different latency/jitter/loss conditions

### Real-Time Monitoring
- **Live Signal Waveform** — Generative canvas art reacting to real signal health
- **Historical Charts** — Chart.js graphs for latency, jitter, packet loss, and QoE over time
- **Sparkline Mini-Charts** — Inline trend lines inside each stat card
- **Latency Heatmap** — Color-coded grid showing latency patterns (green to red)
- **Session Timeline** — Logs quality changes, network events, and root cause alerts

### Advanced Diagnostics
- **Anomaly Detection** — Z-score based spike detection, highlighted on charts with red markers
- **Connection Stability Score** — Coefficient of variation measurement (Rock Solid / Stable / Fluctuating / Unstable)
- **Packet Loss Pattern Analysis** — Distinguishes burst loss vs random loss
- **Traceroute Visualization** — Hop-by-hop network path with per-hop latency bars
- **DNS/TLS/TCP Breakdown** — Performance timing for each connection phase

### Speed Testing
- **Real Download Speed** — Measures actual internet throughput via public CDN downloads (jsdelivr, cdnjs)
- **Upload Speed** — Measures upload throughput to the backend server
- **Multi-Target Ping** — Comparative latency to Google DNS, Cloudflare, and the NetPulse server

### User Experience
- **Dark/Light Theme** — Toggle between dark and light modes
- **Browser Notifications** — Push alerts when network quality drops to "Poor"
- **Sound Alerts** — Audio beep (Web Audio API) on quality drops, with mute toggle
- **Session Persistence** — Data survives page refresh (localStorage)
- **Session History Compare** — Save and compare past monitoring sessions
- **Share Results** — Copy a text summary to clipboard
- **PDF Export** — Print-optimized report via browser print dialog
- **JSON Export** — Download raw session data
- **Smart Recommendations** — Personalized, actionable tips based on current conditions
- **Mobile-Responsive Layout** — Optimized for phone and tablet screens
- **WiFi SVG Favicon** — Custom branded tab icon

---

## 🏗️ Architecture

```
Browser (Client)                          Backend (FastAPI)
┌─────────────────┐                      ┌──────────────────────┐
│ Collect metrics  │  POST /api/metrics   │ Normalize + Window   │
│ via fetch timing │ ──────────────────>  │ Root Cause Analysis  │
│ + navigator API  │                      │ QoE Scoring          │
│                  │  <──────────────────  │ Story Generation     │
│ Render dashboard │  JSON response       │                      │
└─────────────────┘                      └──────────────────────┘
```

**Key Design Decision:** All metric collection happens in the browser using `fetch()` timing and `navigator.connection` API. No OS-level commands (netsh, ping, psutil). This makes the platform fully hostable in the cloud.

---

## 📁 Project Structure

```
├── api/
│   └── main.py              # FastAPI backend (ping, metrics, speed test, traceroute, stability)
├── agent/
│   ├── analyzer.py           # Root cause detection logic
│   ├── normalizer.py         # Metrics windowing and aggregation
│   ├── qoe.py                # QoE scoring + rule-based story engine
│   └── collectors/           # Legacy OS collectors (unused in browser mode)
├── frontend/
│   ├── index.html            # React SPA dashboard (all features)
│   └── favicon.svg           # WiFi SVG icon
├── netpulse.py               # Entry point
├── requirements.txt          # Python dependencies
├── Procfile                  # Render deployment
└── netlify.toml              # Netlify deployment
```

---

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the platform
python netpulse.py

# Open http://localhost:8000 in your browser
```

---

## 🚢 Deployment

### Backend (Render)
1. Create a new **Web Service** on [Render](https://render.com)
2. Connect the GitHub repository
3. Settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app`
4. Environment Variables:
   - `PORT`: 10000

### Frontend (Netlify)
1. Create a new site on [Netlify](https://netlify.com)
2. Set **Base directory** to `frontend/`
3. Set **Publish directory** to `.`
4. **Important**: Update `API_BASE_URL` in `frontend/index.html` to your Render backend URL

---

## 📊 Feature Comparison

| Feature | Basic Ping | Speedtest.net | NetPulse |
|---|---|---|---|
| Latency Monitoring | ✅ | ✅ | ✅ |
| Jitter / Packet Loss | ❌ | ❌ | ✅ |
| Download/Upload Speed | ❌ | ✅ | ✅ |
| Live Historical Charts | ❌ | ❌ | ✅ |
| Anomaly Detection | ❌ | ❌ | ✅ |
| Stability Score | ❌ | ❌ | ✅ |
| Traceroute Visualization | ❌ | ❌ | ✅ |
| Living Signal Waveform | ❌ | ❌ | ✅ |
| WiFi Story (AI Narration) | ❌ | ❌ | ✅ |
| App Quality Profiler | ❌ | ❌ | ✅ |
| "What If" Simulator | ❌ | ❌ | ✅ |
| Root Cause Detection | ❌ | ❌ | ✅ |
| Multi-Target Ping | ❌ | ❌ | ✅ |
| Session Persistence | ❌ | ❌ | ✅ |
| Dark/Light Theme | ❌ | ❌ | ✅ |
| Browser Notifications | ❌ | ❌ | ✅ |

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/ping` | GET | Lightweight ping for latency measurement |
| `/api/metrics/browser` | POST | Ingest browser-collected metrics, run analysis pipeline |
| `/api/metrics/history` | GET | Get last 100 metric frames |
| `/api/speedtest/download` | GET | Download payload for speed measurement |
| `/api/speedtest/upload` | POST | Upload payload for speed measurement |
| `/api/ping/multi` | GET | Multi-target ping (Google DNS, Cloudflare) |
| `/api/traceroute` | GET | Hop-by-hop traceroute to target |
| `/api/stability` | GET | Connection stability score |
| `/api/analyze/story` | POST | Generate WiFi story narrative |
| `/api/export/json` | GET | Download session data as JSON |

---

## 👥 Authors
Team Cognita
