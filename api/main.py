import asyncio
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.normalizer import Normalizer, MetricFrame, WindowedMetrics
from agent.analyzer import Analyzer
from agent.qoe import QoEEngine

app = FastAPI(title="NetPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
normalizer = Normalizer()
analyzer = Analyzer()
qoe_engine = QoEEngine()
metric_history: List[MetricFrame] = []

# Serve Static Files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("frontend/index.html")

# ─── Lightweight ping endpoint for browser latency measurement ───
@app.get("/api/ping")
async def ping():
    return {"t": time.time(), "status": "pong"}

# ─── Browser metrics ingestion ───
class BrowserMetrics(BaseModel):
    latency_ms: float = 0
    jitter_ms: float = 0
    packet_loss_pct: float = 0
    downlink_mbps: float = 0
    rtt_ms: float = 0
    effective_type: str = "4g"
    connection_type: str = "wifi"

@app.post("/api/metrics/browser")
async def ingest_browser_metrics(metrics: BrowserMetrics):
    """Receives metrics collected by the browser, runs the full analysis pipeline."""
    
    # Map browser metrics to a MetricFrame
    latency = metrics.latency_ms if metrics.latency_ms > 0 else metrics.rtt_ms
    downlink = metrics.downlink_mbps
    
    # Estimate RSSI from effective connection type
    rssi_map = {"4g": -45, "3g": -65, "2g": -80, "slow-2g": -90}
    rssi = rssi_map.get(metrics.effective_type, -50)
    
    # Estimate SNR from RSSI (noise floor ~ -95dBm)
    snr = rssi - (-95)
    
    frame = MetricFrame(
        timestamp=datetime.now(),
        ssid=f"WiFi ({metrics.effective_type})" if metrics.connection_type == "wifi" else metrics.connection_type,
        bssid="browser",
        channel=0,
        band=metrics.connection_type,
        rssi_dbm=rssi,
        noise_floor_dbm=-95,
        snr_db=snr,
        tx_rate_mbps=downlink,
        rx_rate_mbps=downlink,
        latency_ms=latency,
        jitter_ms=metrics.jitter_ms,
        packet_loss_pct=metrics.packet_loss_pct,
        platform="browser",
    )
    
    # Run analysis pipeline
    metric_history.append(frame)
    if len(metric_history) > 1000:
        metric_history.pop(0)
    
    windowed = normalizer.ingest(frame)
    causes = analyzer.detect_causes(metric_history[-10:], windowed)
    qoe = qoe_engine.compute_score(windowed)
    
    return {
        "current": frame.model_dump(),
        "windowed": windowed.model_dump(),
        "causes": [c.model_dump() for c in causes],
        "qoe": qoe.model_dump()
    }

@app.get("/api/metrics/history")
async def get_history():
    return metric_history[-100:]

@app.get("/api/export/json")
async def export_json():
    return JSONResponse(content=[f.model_dump() for f in metric_history], headers={
        "Content-Disposition": "attachment; filename=netpulse_session.json"
    })

@app.post("/api/analyze/story")
async def get_story():
    if not metric_history:
        return {"story": "No metrics collected yet. Wait a few seconds for data to start flowing."}

    windowed = normalizer._compute_windowed_metrics()
    causes = analyzer.detect_causes(metric_history[-10:], windowed)
    
    story = await qoe_engine.generate_story(
        json.dumps(windowed.model_dump(), default=str),
        json.dumps([c.model_dump() for c in causes], default=str)
    )
    
    return {"story": story}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
