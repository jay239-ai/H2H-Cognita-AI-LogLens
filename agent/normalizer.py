from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class MetricFrame(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    ssid: str
    bssid: str
    channel: int
    band: str  # 2.4/5/6 GHz
    rssi_dbm: int
    noise_floor_dbm: int = -95  # Default fallback
    snr_db: int
    tx_rate_mbps: float
    rx_rate_mbps: float
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    platform: str
    nearby_ap_count: int = 0
    cpu_usage: float = 0
    ram_usage: float = 0

class WindowedMetrics(BaseModel):
    mean_latency: float
    p95_jitter: float
    packet_loss_pct: float
    snr_trend: float  # Slope of SNR
    throughput_utilization: float

class Normalizer:
    def __init__(self, window_size_seconds: int = 30):
        self.window_size_seconds = window_size_seconds
        self.metrics_history: List[MetricFrame] = []

    def ingest(self, frame: MetricFrame) -> WindowedMetrics:
        self.metrics_history.append(frame)
        self._prune_history()
        return self._compute_windowed_metrics()

    def _prune_history(self):
        now = datetime.now()
        self.metrics_history = [
            f for f in self.metrics_history 
            if (now - f.timestamp).total_seconds() <= self.window_size_seconds
        ]

    def _compute_windowed_metrics(self) -> WindowedMetrics:
        if not self.metrics_history:
            return WindowedMetrics(
                mean_latency=0, p95_jitter=0, packet_loss_pct=0, 
                snr_trend=0, throughput_utilization=0
            )

        latencies = [f.latency_ms for f in self.metrics_history]
        jitters = [f.jitter_ms for f in self.metrics_history]
        losses = [f.packet_loss_pct for f in self.metrics_history]
        snrs = [f.snr_db for f in self.metrics_history]
        
        # Simple trend (difference between last and first SNR in window)
        snr_trend = (snrs[-1] - snrs[0]) if len(snrs) > 1 else 0
        
        # Throughput utilization (basic ratio of current vs max rate in window)
        tx_rates = [f.tx_rate_mbps for f in self.metrics_history]
        max_rate = max(tx_rates) if tx_rates else 1
        utilization = tx_rates[-1] / max_rate if max_rate > 0 else 0

        import numpy as np
        return WindowedMetrics(
            mean_latency=float(np.mean(latencies)),
            p95_jitter=float(np.percentile(jitters, 95)) if jitters else 0,
            packet_loss_pct=float(np.mean(losses)),
            snr_trend=float(snr_trend),
            throughput_utilization=float(utilization)
        )
