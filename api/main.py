import asyncio
import json
import os
import sys
import time
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, Response
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
    expose_headers=["X-Server-Timing"],
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

# ─── Lightweight ping for latency measurement ───
@app.get("/api/ping")
async def ping():
    return {"t": time.time(), "status": "pong"}

# ─── Speed Test Endpoints ───
@app.get("/api/speedtest/download")
async def speedtest_download(size: int = 1):
    """Returns a payload of `size` MB for download speed measurement."""
    size_mb = max(1, min(size, 10))  # Clamp between 1-10 MB
    chunk_size = 65536  # 64KB chunks
    total_bytes = size_mb * 1024 * 1024

    def generate():
        sent = 0
        chunk = os.urandom(chunk_size)
        while sent < total_bytes:
            remaining = total_bytes - sent
            if remaining < chunk_size:
                yield chunk[:remaining]
                sent += remaining
            else:
                yield chunk
                sent += chunk_size

    return StreamingResponse(
        generate(),
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(total_bytes),
            "Cache-Control": "no-store",
            "X-Payload-Size": str(total_bytes),
        }
    )

@app.post("/api/speedtest/upload")
async def speedtest_upload(request: Request):
    """Receives an upload payload and reports how much was received."""
    start = time.time()
    body = await request.body()
    elapsed = time.time() - start
    size_bytes = len(body)
    speed_mbps = (size_bytes * 8 / (1024 * 1024)) / elapsed if elapsed > 0 else 0
    return {
        "bytes_received": size_bytes,
        "elapsed_seconds": round(elapsed, 4),
        "speed_mbps": round(speed_mbps, 2),
    }

# ─── Multi-Target Ping (server-side timing) ───
@app.get("/api/ping/multi")
async def multi_ping():
    """Returns server-side timing to multiple DNS targets for comparison."""
    import httpx
    targets = [
        {"name": "Google DNS", "url": "https://dns.google/resolve?name=example.com&type=A"},
        {"name": "Cloudflare", "url": "https://cloudflare-dns.com/dns-query?name=example.com&type=A"},
        {"name": "NetPulse Server", "url": None},  # Local timing
    ]
    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for target in targets:
            if target["url"] is None:
                results.append({"name": target["name"], "latency_ms": 0.1, "status": "ok"})
                continue
            try:
                start = time.time()
                resp = await client.get(target["url"], headers={"Accept": "application/dns-json"})
                elapsed = (time.time() - start) * 1000
                results.append({
                    "name": target["name"],
                    "latency_ms": round(elapsed, 2),
                    "status": "ok" if resp.status_code == 200 else "error"
                })
            except Exception as e:
                results.append({"name": target["name"], "latency_ms": -1, "status": str(e)[:50]})
    return results

# ─── Browser Metrics Ingestion ───
class BrowserMetrics(BaseModel):
    latency_ms: float = 0
    jitter_ms: float = 0
    packet_loss_pct: float = 0
    downlink_mbps: float = 0
    rtt_ms: float = 0
    effective_type: str = "4g"
    connection_type: str = "wifi"
    dns_ms: float = 0
    tls_ms: float = 0
    tcp_ms: float = 0

@app.post("/api/metrics/browser")
async def ingest_browser_metrics(metrics: BrowserMetrics):
    """Receives browser-collected metrics, runs analysis pipeline."""
    latency = metrics.latency_ms if metrics.latency_ms > 0 else metrics.rtt_ms
    downlink = metrics.downlink_mbps

    rssi_map = {"4g": -45, "3g": -65, "2g": -80, "slow-2g": -90}
    rssi = rssi_map.get(metrics.effective_type, -50)
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
        "qoe": qoe.model_dump(),
        "timing": {
            "dns_ms": metrics.dns_ms,
            "tls_ms": metrics.tls_ms,
            "tcp_ms": metrics.tcp_ms,
        }
    }

@app.get("/api/metrics/history")
async def get_history():
    return metric_history[-100:]

@app.get("/api/export/json")
async def export_json():
    return JSONResponse(
        content=[f.model_dump() for f in metric_history],
        headers={"Content-Disposition": "attachment; filename=netpulse_session.json"}
    )

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

@app.get("/api/traceroute")
async def traceroute(target: str = "8.8.8.8"):
    """Runs traceroute and returns hop-by-hop data."""
    import subprocess, re, platform as plat
    hops = []
    try:
        if plat.system() == "Windows":
            cmd = ["tracert", "-d", "-w", "1000", "-h", "15", target]
        else:
            cmd = ["traceroute", "-n", "-w", "1", "-m", "15", target]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = proc.stdout
        
        for line in output.split('\n'):
            line = line.strip()
            if not line or 'Tracing' in line or 'over' in line or 'trace' in line:
                continue
            # Parse hop number and RTT values
            match = re.match(r'^\s*(\d+)\s+(.+)$', line)
            if match:
                hop_num = int(match.group(1))
                rest = match.group(2)
                # Extract IP
                ip_match = re.findall(r'(\d+\.\d+\.\d+\.\d+)', rest)
                ip = ip_match[-1] if ip_match else '*'
                # Extract RTT values
                rtt_vals = re.findall(r'(\d+)\s*ms', rest)
                avg_rtt = sum(float(r) for r in rtt_vals) / len(rtt_vals) if rtt_vals else -1
                
                hops.append({
                    "hop": hop_num,
                    "ip": ip,
                    "rtt_ms": round(avg_rtt, 1),
                    "status": "ok" if avg_rtt >= 0 else "timeout"
                })
    except subprocess.TimeoutExpired:
        hops.append({"hop": 0, "ip": "timeout", "rtt_ms": -1, "status": "Traceroute timed out"})
    except Exception as e:
        hops.append({"hop": 0, "ip": "error", "rtt_ms": -1, "status": str(e)[:80]})
    
    return hops

@app.get("/api/stability")
async def stability_score():
    """Computes connection stability from recent metrics."""
    if len(metric_history) < 5:
        return {"stability": 100, "label": "Insufficient Data", "samples": len(metric_history)}
    
    import numpy as np
    recent = metric_history[-30:]
    latencies = [f.latency_ms for f in recent]
    jitters = [f.jitter_ms for f in recent]
    losses = [f.packet_loss_pct for f in recent]
    
    # Coefficient of Variation (lower = more stable)
    lat_cv = (np.std(latencies) / np.mean(latencies) * 100) if np.mean(latencies) > 0 else 0
    jit_cv = (np.std(jitters) / np.mean(jitters) * 100) if np.mean(jitters) > 0 else 0
    
    # Stability = 100 - weighted CV (capped)
    stability = max(0, min(100, 100 - (0.5 * lat_cv + 0.3 * jit_cv + 0.2 * np.mean(losses) * 10)))
    label = "Rock Solid" if stability >= 85 else "Stable" if stability >= 65 else "Fluctuating" if stability >= 40 else "Unstable"
    
    return {
        "stability": round(stability, 1),
        "label": label,
        "samples": len(recent),
        "latency_cv": round(lat_cv, 1),
        "jitter_cv": round(jit_cv, 1),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
