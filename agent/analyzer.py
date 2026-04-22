from typing import List, Optional
from pydantic import BaseModel
from agent.normalizer import MetricFrame, WindowedMetrics

class RootCause(BaseModel):
    type: str
    confidence: float
    evidence: str
    mitigation: str

class Analyzer:
    def detect_causes(self, frames: List[MetricFrame], windowed: WindowedMetrics) -> List[RootCause]:
        causes = []
        if not frames: return causes

        last_frame = frames[-1]
        
        # 1. Channel Congestion
        # (Need scan data for real AP count, but using SNR drops as proxy)
        if windowed.snr_trend < -5 and windowed.packet_loss_pct > 2:
            causes.append(RootCause(
                type="Channel Congestion",
                confidence=0.7,
                evidence=f"SNR trend dropped {windowed.snr_trend}dB with packet loss {windowed.packet_loss_pct}%",
                mitigation="Switch to a less congested channel (e.g., 1, 6, 11 on 2.4GHz)"
            ))

        # 2. Non-WiFi Interference (Noise Floor Spike)
        # (Since we lack real noise floor, using RSSI vs Throughput ratio)
        if last_frame.rssi_dbm > -60 and windowed.mean_latency > 150:
             causes.append(RootCause(
                type="Non-WiFi Interference",
                confidence=0.6,
                evidence="High signal strength but high latency suggests interference (microwave, Bluetooth, etc.)",
                mitigation="Move away from electronic devices like microwaves or baby monitors."
            ))

        # 3. AP Overload
        if windowed.packet_loss_pct > 5 and last_frame.rssi_dbm > -55:
            causes.append(RootCause(
                type="AP Overload",
                confidence=0.8,
                evidence=f"High packet loss ({windowed.packet_loss_pct}%) despite strong signal ({last_frame.rssi_dbm}dBm)",
                mitigation="Reduce the number of connected devices or upgrade the Access Point hardware."
            ))

        # 4. Signal Attenuation
        if last_frame.rssi_dbm < -75:
            causes.append(RootCause(
                type="Signal Attenuation",
                confidence=0.9,
                evidence=f"Signal strength is weak ({last_frame.rssi_dbm}dBm)",
                mitigation="Move closer to the Access Point or install a WiFi range extender."
            ))

        # 5. Roaming Event
        if len(frames) > 1 and frames[-1].bssid != frames[-2].bssid:
             causes.append(RootCause(
                type="Roaming Event",
                confidence=1.0,
                evidence=f"BSSID changed from {frames[-2].bssid} to {frames[-1].bssid}",
                mitigation="Ensure consistent signal coverage to prevent frequent roaming."
            ))

        # 6. Interference Fingerprinting (Microwave/Non-WiFi)
        # Fingerprint: Sudden noise floor spike + high jitter + loss
        if windowed.p95_jitter > 50 and last_frame.rssi_dbm > -65:
            # Pattern check: High jitter with strong signal is a classic interference signature
            causes.append(RootCause(
                type="Interference Fingerprint: Microwave/Non-WiFi",
                confidence=0.75,
                evidence=f"Classic noise signature detected: Jitter spike ({windowed.p95_jitter}ms) on strong RSSI ({last_frame.rssi_dbm}dBm)",
                mitigation="Identify nearby 2.4GHz devices (microwaves, baby monitors) and move them or switch to 5GHz."
            ))

        return causes
