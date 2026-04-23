# NetPulse

**Real-time, browser-based WiFi quality analyzer with live diagnostics, speed testing, and intelligent network analysis.**

NetPulse monitors your network connection from the browser, scores its quality in real time, detects root causes of degradation, and provides actionable recommendations. No installs, no OS-level access. Fully deployable on Render + Netlify.

**Live Demo**: [cognita-netpulse.netlify.app](https://cognita-netpulse.netlify.app)

---

## Architecture

```
  BROWSER (Client)                          RENDER (Server)
  ================                          ================

  Metrics Collector                         FastAPI Backend
  - ping cloudflare.com/cdn-cgi/trace       - Normalizer (30s window)
  - navigator.connection API                - Root Cause Analyzer
  - PerformanceResourceTiming               - QoE Scoring Engine
         |                                  - Story Generator
         | POST /api/metrics/browser              |
         +--------------------------------------->+
         |                                        |
         |<---------------------------------------+
         |  { current, qoe, causes, profiles }
         |
  Client-Side Only
  - Speed test (Cloudflare __down/__up)
  - Multi-target ping (browser fetch)
  - Stability score (computed from history)
  - Network path trace (browser fetch)
  - JSON export (Blob download)
  - All UI rendering (React 18 + Chart.js)
```

All metric collection runs in the browser. The server handles normalization, analysis, and scoring. Speed tests, multi-ping, stability, network path, and export all work without the backend.

---

## Features

### Core Intelligence

| Feature | Description |
|---|---|
| QoE Score | Weighted quality score (latency 35%, jitter 25%, loss 25%, throughput 15%) displayed as animated SVG gauge |
| Root Cause Analysis | Detects congestion, interference, distance, and hardware issues with evidence and fixes |
| WiFi Story Mode | Rule-based narrative engine that describes your network in plain English |
| App Profiler | Rates Video Calls, Gaming, Streaming, and Browsing independently |
| What-If Simulator | Slider-based prediction of QoE under custom latency/jitter/loss conditions |

### Real-Time Monitoring

| Feature | Description |
|---|---|
| Live Metrics | Latency, jitter, packet loss, downlink refreshed every 3 seconds |
| Signal Waveform | Animated HTML5 Canvas that reacts to signal health in real time |
| Historical Charts | 4 Chart.js line graphs (latency, jitter, loss, QoE) with 60-point rolling window |
| Sparkline Charts | Inline 20-point trend lines inside each stat card |
| Latency Heatmap | Color-coded grid (green to red) showing latency distribution over time |
| Session Timeline | Chronological log of quality changes, detected issues, and connection events |

### Diagnostics

| Feature | Description |
|---|---|
| Anomaly Detection | Z-score based spike detection (threshold > 2.0) highlighted as red dots on charts |
| Stability Score | Client-side coefficient of variation (CV) of latency and jitter, labeled Rock Solid / Stable / Fluctuating / Unstable |
| Loss Pattern Analysis | Classifies packet loss as burst (hardware), random (congestion), or mixed |
| Network Path Trace | Browser-based ping to 7 global endpoints (Cloudflare, Google, AWS, Microsoft, Fastly) with 3-ping median |
| DNS/TLS/TCP Breakdown | Connection phase timing from PerformanceResourceTiming API using CORS-enabled fetch |

### Speed Testing

| Feature | Description |
|---|---|
| Download | Cloudflare `speed.cloudflare.com/__down` with progressive sizes (100KB to 10MB), streaming byte count |
| Upload | Cloudflare `speed.cloudflare.com/__up` with 2MB random payload, requires `CF-Speed-Test` header |
| Multi-Target Ping | Client-side latency comparison across Cloudflare DNS, Google DNS, Cloudflare Edge, Google Edge, Amazon CDN |

### Network Info

| Feature | Description |
|---|---|
| Connection Type | WiFi / Cellular / Ethernet from navigator.connection (N/A on Firefox/Safari) |
| Speed Class | 4G / 3G / 2G from navigator.connection.effectiveType |
| ISP / IP / Location | Fetched from ipapi.co with ip-api.com fallback |

### UX and Persistence

| Feature | Description |
|---|---|
| Dark/Light Theme | Toggle with localStorage persistence |
| Push Notifications | Browser notification when QoE drops to Poor |
| Sound Alerts | 440Hz sine wave via Web Audio API on quality drops, toggleable |
| Session Persistence | History (120 entries), events (50), sample count saved to localStorage every 5 seconds |
| Session Compare | Save snapshots and compare past sessions |
| Share | Copy formatted text report to clipboard |
| PDF Export | Print-optimized layout via browser print dialog |
| JSON Export | Client-side Blob download with full history, events, current metrics, and QoE data |
| Recommendations | Context-aware tips based on current latency, jitter, loss, and app profiles |
| Mobile Responsive | Grid layout adapts to phone and tablet screens |

---

## Project Structure

```
H2H-Cognita-AI-LogLens/
|
|-- api/
|   |-- main.py                 # FastAPI backend, all API routes
|
|-- agent/
|   |-- analyzer.py             # Root cause detection engine
|   |-- normalizer.py           # Metrics windowing (30s sliding window)
|   |-- qoe.py                  # QoE scoring + rule-based story generator
|   |-- collectors/             # Legacy OS-level collectors (unused)
|
|-- frontend/
|   |-- index.html              # React 18 SPA (all UI components)
|   |-- favicon.svg             # WiFi SVG icon
|   |-- netlify.toml            # Netlify deployment config
|
|-- netpulse.py                 # Local entry point
|-- requirements.txt            # Python dependencies
|-- Procfile                    # Render deployment command
|-- IMPLEMENTATION.md           # Detailed technical reference
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (CDN), Babel (JSX transform), Tailwind CSS (CDN), Chart.js 4 |
| Backend | Python 3.11, FastAPI, Uvicorn, Gunicorn |
| Analysis | Custom Python engines (normalizer, analyzer, QoE scorer) |
| Speed Test | Cloudflare speed test endpoints |
| Deployment | Render (backend), Netlify (frontend) |
| Dependencies | fastapi, uvicorn, pydantic, python-dotenv, gunicorn, httpx, numpy |

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/jay239-ai/H2H-Cognita-AI-LogLens.git
cd H2H-Cognita-AI-LogLens

# Install Python dependencies
pip install -r requirements.txt

# Start the server
python netpulse.py

# Open http://localhost:8000
```

The frontend is served by FastAPI from the `frontend/` directory. No separate frontend build step is needed.

---

## Deployment

### Backend on Render

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect the GitHub repository
3. Configure:

| Setting | Value |
|---|---|
| Environment | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app` |
| Port | 10000 |

### Frontend on Netlify

1. Create a new site on [netlify.com](https://netlify.com)
2. Connect the same GitHub repository
3. Configure:

| Setting | Value |
|---|---|
| Base directory | `frontend` |
| Publish directory | `frontend` |
| Build command | (leave empty) |

4. Update `API_BASE_URL` in `frontend/index.html` to your Render backend URL:
```js
const API_BASE_URL = 'https://your-app.onrender.com';
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/ping` | GET | Lightweight latency measurement |
| `/api/metrics/browser` | POST | Ingest metrics, run full analysis pipeline, return results |
| `/api/metrics/history` | GET | Last 100 metric frames |
| `/api/speedtest/download` | GET | Download payload for speed measurement |
| `/api/speedtest/upload` | POST | Upload timing measurement |
| `/api/ping/multi` | GET | Multi-target ping from server |
| `/api/analyze/story` | POST | Generate WiFi story narrative |

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for request/response schemas and algorithm details.

---

## Browser Compatibility

| Feature | Chrome/Edge | Firefox | Safari |
|---|---|---|---|
| Core metrics (fetch timing) | Full | Full | Full |
| navigator.connection API | Full | Not supported (shows N/A) | Not supported (shows N/A) |
| Speed test (Cloudflare) | Full | Full | Full |
| Push notifications | Full | Full | Full |
| PerformanceResourceTiming | Full (cors mode) | Full (cors mode) | Full (cors mode) |

---

## Feature Comparison

| Capability | Basic Ping | Speedtest.net | NetPulse |
|---|---|---|---|
| Latency monitoring | Yes | Yes | Yes |
| Jitter / packet loss | No | No | Yes |
| Download/upload speed | No | Yes | Yes |
| Live historical charts | No | No | Yes |
| Anomaly detection | No | No | Yes |
| Stability scoring | No | No | Yes |
| Network path trace | No | No | Yes |
| Signal waveform | No | No | Yes |
| WiFi story narration | No | No | Yes |
| App quality profiler | No | No | Yes |
| What-If simulator | No | No | Yes |
| Root cause detection | No | No | Yes |
| Multi-target ping | No | No | Yes |
| Session persistence | No | No | Yes |
| JSON/PDF export | No | No | Yes |

---

## Authors

**Team Cognita**
