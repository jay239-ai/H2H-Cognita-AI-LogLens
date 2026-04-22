import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from agent.normalizer import WindowedMetrics
from google import genai

class QoEScore(BaseModel):
    total_score: float
    label: str  # Good, Moderate, Poor
    app_profiles: Dict[str, str]
    simulation: Optional[Dict[str, float]] = None

class QoEEngine:
    def __init__(self, gemini_api_key: str = None):
        # Explicitly reload .env in case it was modified after start
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        # Priority: passed key > .env key > hardcoded fallback for hackathon
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or "AIzaSyAVdAU2N2khQXGJt9Zwj5TAO0Xkfb_NT74"
        
        try:
            self.client = genai.Client(api_key=self.gemini_api_key)
        except Exception as e:
            print(f"⚠️ Failed to configure Gemini: {e}")
            self.client = None

    def compute_score(self, metrics: WindowedMetrics, simulation_params: Dict = None) -> QoEScore:
        # Use simulation params if provided (What If Simulator)
        latency = simulation_params.get("latency", metrics.mean_latency) if simulation_params else metrics.mean_latency
        jitter = simulation_params.get("jitter", metrics.p95_jitter) if simulation_params else metrics.p95_jitter
        loss = simulation_params.get("loss", metrics.packet_loss_pct) if simulation_params else metrics.packet_loss_pct
        snr_trend = simulation_params.get("snr_trend", metrics.snr_trend) if simulation_params else metrics.snr_trend

        # Score calculation weights: 35% latency, 25% jitter, 25% loss, 15% SNR trend
        latency_score = max(0, 100 - latency / 2)
        jitter_score = max(0, 100 - jitter * 2)
        loss_score = max(0, 100 - loss * 10)
        snr_score = min(100, 50 + snr_trend * 5)

        total_score = (
            0.35 * latency_score + 
            0.25 * jitter_score + 
            0.25 * loss_score + 
            0.15 * snr_score
        )

        label = "Good" if total_score >= 75 else "Moderate" if total_score >= 45 else "Poor"

        app_profiles = {
            "Video Call": self._evaluate_app(latency, jitter, loss, snr_trend, "video"),
            "Gaming": self._evaluate_app(latency, jitter, loss, snr_trend, "gaming"),
            "Streaming": self._evaluate_app(latency, jitter, loss, snr_trend, "streaming")
        }

        # Predict improved score if packet loss was 0 (What If)
        predicted_score = None
        if not simulation_params:
            sim_score = self.compute_score(metrics, {"latency": latency, "jitter": jitter, "loss": 0, "snr_trend": snr_trend})
            predicted_score = {"perfect_loss_score": sim_score.total_score}

        return QoEScore(
            total_score=total_score, 
            label=label, 
            app_profiles=app_profiles,
            simulation=predicted_score
        )

    def _evaluate_app(self, latency, jitter, loss, snr_trend, app_type: str) -> str:
        if app_type == "video":
            # Latency < 150ms, Jitter < 30ms, Loss < 1%
            if latency < 150 and jitter < 30 and loss < 1:
                return "Excellent"
            return "Laggy"
        
        if app_type == "gaming":
            # Latency < 50ms, Jitter < 10ms, Loss < 0.5%
            if latency < 50 and jitter < 10 and loss < 0.5:
                return "Fluid"
            return "Unplayable"
        
        if app_type == "streaming":
            # Loss < 2%, SNRTrend not dropping fast
            if loss < 2 and snr_trend > -10:
                return "Stable"
            return "Buffering"

        return "Unknown"

    def generate_rule_based_story(self, metrics: WindowedMetrics, causes: list, current_frame=None) -> str:
        """Generates a personalized, human-readable WiFi story from metrics and root causes — no API needed."""
        
        parts = []
        
        # --- Part 1: What happened ---
        lat = metrics.mean_latency
        jit = metrics.p95_jitter
        loss = metrics.packet_loss_pct
        snr = metrics.snr_trend
        
        if lat < 30 and jit < 10 and loss < 1:
            what = f"Your connection has been rock-solid — averaging {lat:.0f}ms latency with virtually no packet loss ({loss:.1f}%)."
        elif lat < 80 and loss < 3:
            what = f"Your connection is holding up reasonably well at {lat:.0f}ms average latency, though there's some jitter ({jit:.0f}ms) causing minor hiccups."
        elif lat < 150:
            what = f"Your network is under strain — latency has climbed to {lat:.0f}ms with {loss:.1f}% packet loss and {jit:.0f}ms of jitter."
        else:
            what = f"Your connection is struggling badly — {lat:.0f}ms latency, {jit:.0f}ms jitter, and {loss:.1f}% packet loss paint a rough picture."
        parts.append(what)
        
        # --- Part 2: Why it happened (from root causes) ---
        if causes:
            cause_names = [c.type if hasattr(c, 'type') else c.get('type', 'Unknown') for c in causes]
            evidence_list = [c.evidence if hasattr(c, 'evidence') else c.get('evidence', '') for c in causes]
            
            if len(cause_names) == 1:
                why = f"The likely culprit is {cause_names[0].lower()} — {evidence_list[0].lower()}."
            else:
                top_causes = ', '.join(cause_names[:2])
                why = f"Multiple issues detected: {top_causes}. {evidence_list[0]}."
        else:
            if snr > 2:
                why = "Signal quality is actually improving — the SNR trend is positive, so conditions are getting better."
            elif snr < -3:
                why = f"The signal-to-noise ratio has been dropping (trend: {snr:+.1f}dB), which often means growing interference or distance from the router."
            else:
                why = "No specific root cause was detected — the network environment appears stable."
        parts.append(why)
        
        # --- Part 3: What the user experienced ---
        # Build app-specific impact
        impacts = []
        if lat > 150 or jit > 30 or loss > 1:
            impacts.append("video calls would feel laggy with potential freezing")
        if lat > 50 or jit > 10 or loss > 0.5:
            impacts.append("online gaming would suffer from noticeable input delay")
        if loss > 2 or snr < -10:
            impacts.append("streaming video might buffer frequently")
        
        if not impacts:
            experience = "In practical terms, you should have a smooth experience across video calls, gaming, and streaming — everything looks great."
        elif len(impacts) == 1:
            experience = f"In practical terms, {impacts[0]}."
        else:
            experience = f"In practical terms, {impacts[0]}, and {impacts[1]}."
        
        # Add a personalized tip from the top root cause
        if causes:
            top_mitigation = causes[0].mitigation if hasattr(causes[0], 'mitigation') else causes[0].get('mitigation', '')
            if top_mitigation:
                experience += f" 💡 Tip: {top_mitigation}"
        
        parts.append(experience)
        
        return " ".join(parts)

    async def generate_story(self, metrics_json: str, root_causes_json: str) -> str:
        """Kept for API compatibility — delegates to rule-based engine."""
        import json as _json
        try:
            metrics_dict = _json.loads(metrics_json)
            causes_list = _json.loads(root_causes_json)
            metrics = WindowedMetrics(**metrics_dict)
            return self.generate_rule_based_story(metrics, causes_list)
        except Exception as e:
            return f"Analysis error: {str(e)}"
