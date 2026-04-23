# NetPulse: Implementation Details

This document provides a deep technical reference for every component, algorithm, and data flow in the NetPulse platform.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Metrics Collection Pipeline](#metrics-collection-pipeline)
3. [QoE Scoring Algorithm](#qoe-scoring-algorithm)
4. [Root Cause Analysis Engine](#root-cause-analysis-engine)
5. [Speed Test Implementation](#speed-test-implementation)
6. [Anomaly Detection](#anomaly-detection)
7. [Stability Score Calculation](#stability-score-calculation)
8. [Network Path Trace](#network-path-trace)
9. [Packet Loss Pattern Analysis](#packet-loss-pattern-analysis)
10. [WiFi Story Generator](#wifi-story-generator)
11. [Frontend Components](#frontend-components)
12. [Backend API Reference](#backend-api-reference)
13. [Browser API Compatibility](#browser-api-compatibility)
14. [Data Persistence](#data-persistence)

---

## System Architecture

```
                        NetPulse Architecture
                        
  Browser (Client-Side)                    Render (Server-Side)
  =====================                    ====================

  +-------------------+                    +--------------------+
  | Metrics Collector  |    POST /api/     | FastAPI Backend     |
  | - fetch() timing   | -- metrics/ ---> | - Normalizer        |
  | - navigator.conn   |    browser        | - 30s window agg   |
  | - Performance API  |                  | - Analyzer          |
  +-------------------+                    | - QoE Engine        |
          |                                +--------------------+
          v                                        |
  +-------------------+                            |
  | Client-Side Only   |    <-- JSON response -----+
  | - Speed Test (CF)  |
  | - Multi-Ping       |     Analysis result:
  | - Stability Score  |     {current, qoe, causes,
  | - Network Path     |      story, app_profiles}
  | - Export JSON       |
  +-------------------+
          |
          v
  +-------------------+
  | Dashboard Renderer |
  | - React 18 SPA     |
  | - Chart.js graphs  |
  | - Canvas waveform  |
  | - localStorage     |
  +-------------------+
```

### Data Flow

1. Every 3 seconds, the browser collects metrics by pinging `cloudflare.com/cdn-cgi/trace`
2. Raw metrics (latency, jitter, packet loss, downlink) are sent to the backend via `POST /api/metrics/browser`
3. The backend normalizes the data into a 30-second sliding window
4. The Analyzer engine runs root cause detection on the windowed data
5. The QoE engine scores the connection and generates app profiles
6. The full analysis is returned as JSON to the browser
7. React re-renders all dashboard components with the new data

### What runs where

| Component | Runs On | Why |
|---|---|---|
| Latency/Jitter/Loss collection | Browser | Must measure from user's actual network, not server |
| Speed test (download + upload) | Browser via Cloudflare | Measures real throughput to nearest edge |
| Multi-target ping | Browser | Measures user's latency to each target |
| Stability score | Browser | Computed from client-side history array |
| Network path trace | Browser | Pings global endpoints from user's browser |
| Export JSON | Browser | Downloads from in-memory state |
| Normalization + windowing | Server | Stateful 30s sliding window across requests |
| Root cause analysis | Server | Needs historical context from multiple frames |
| QoE scoring | Server | Complex weighted algorithm with app profiles |
| Story generation | Server | Rule-based engine needs full analysis context |

---

## Metrics Collection Pipeline

### Source: `collectMetrics()` in `frontend/index.html`

```
Ping Target: https://www.cloudflare.com/cdn-cgi/trace
Mode: cors (enables PerformanceResourceTiming)
Ping Count: 10 (1 warm-up + 9 real)
Timeout: 1000ms per ping
```

### Why Cloudflare?

- CORS enabled: Returns proper `PerformanceResourceTiming` entries (DNS, TCP, TLS values)
- Edge-served: Cloudflare has PoPs in 300+ cities, so latency reflects local network quality
- No caching: Each request with cache-busting query param gets a fresh response
- Reliable: 99.99% uptime

### Measurement Process

1. **Warm-up ping (discarded)**: First fetch incurs DNS lookup, TCP handshake, and TLS negotiation overhead. This is not representative of steady-state latency.
2. **9 real pings**: Each measured with `performance.now()` for sub-millisecond precision
3. **Latency**: Arithmetic mean of the 9 pings
4. **Jitter**: Mean absolute deviation from the mean (MAD)
5. **Packet loss**: Count of failed/timed-out pings divided by 9, as percentage

### navigator.connection API

The `NetworkInformation` API provides:
- `rtt`: Round-trip time estimate (rounded to 25ms increments)
- `downlink`: Estimated bandwidth in Mbps
- `effectiveType`: '4g', '3g', '2g', 'slow-2g'
- `type`: 'wifi', 'cellular', 'ethernet', 'bluetooth'

**Browser support**: Chrome/Edge/Opera only. Firefox and Safari do not support this API. The app detects this and shows "N/A" instead of silently defaulting.

### DNS/TLS/TCP Timing

Because we use `mode: 'cors'` (not `no-cors`), the browser exposes full `PerformanceResourceTiming` entries:
- `domainLookupEnd - domainLookupStart` = DNS resolution time
- `connectEnd - connectStart` = TCP handshake time
- `connectEnd - secureConnectionStart` = TLS negotiation time

With `no-cors`, these values are always 0 due to the Timing-Allow-Origin restriction.

---

## QoE Scoring Algorithm

### Source: `agent/qoe.py`

```python
QoE = (0.35 * latency_score) + (0.25 * jitter_score) + (0.25 * loss_score) + (0.15 * throughput_score)
```

### Individual Scores (0-100 scale)

| Metric | Formula |
|---|---|
| Latency | `max(0, 100 - (latency_ms / 2))` |
| Jitter | `max(0, 100 - (jitter_ms * 2))` |
| Packet Loss | `max(0, 100 - (loss_pct * 10))` |
| Throughput | `min(100, (throughput_mbps / 50) * 100)` |

### Labels

| Score Range | Label | Gauge Color |
|---|---|---|
| 75 - 100 | Good | Green (#10B981) |
| 45 - 74 | Moderate | Yellow (#F59E0B) |
| 0 - 44 | Poor | Red (#EF4444) |

### App Profiles

| Application | Good Condition | Degraded Condition |
|---|---|---|
| Video Call | Latency < 150ms, Loss < 1% | Otherwise "Laggy" |
| Gaming | Latency < 50ms, Jitter < 10ms | Otherwise "Unplayable" |
| Streaming | Downlink > 5 Mbps | Otherwise "Buffering" |
| Browsing | Latency < 200ms | Otherwise "Slow" |

---

## Root Cause Analysis Engine

### Source: `agent/analyzer.py`

The analyzer examines windowed metrics and returns an array of detected issues, each with:
- `type`: Category of issue (e.g., "Congestion", "Interference")
- `evidence`: What data triggered the detection
- `mitigation`: Recommended fix

### Detection Rules

| Cause | Trigger Condition | Mitigation |
|---|---|---|
| Congestion | High latency + low throughput | Close bandwidth-heavy apps, check other devices |
| Interference | Jitter spikes + signal drops | Switch to 5GHz band, relocate router |
| Distance | Weak signal + moderate latency | Move closer to router |
| Hardware | Burst packet loss pattern | Restart router, check cables |

---

## Speed Test Implementation

### Download Test

```
Endpoint: https://speed.cloudflare.com/__down?bytes={size}
Sizes: 100KB, 1MB, 5MB, 10MB (sequential)
Method: Streaming read via ReadableStream
Calculation: (total_bytes * 8) / (elapsed_seconds * 1024 * 1024) = Mbps
```

Cloudflare's `__down` endpoint serves random bytes with no caching, making it ideal for throughput measurement. The progressive size increase (100KB to 10MB) helps warm up the connection and provides an accurate sustained throughput reading.

### Upload Test

```
Endpoint: https://speed.cloudflare.com/__up
Method: POST with 2MB random payload
Headers: CF-Speed-Test: 1, Content-Type: application/octet-stream
Calculation: (payload_bytes * 8) / (elapsed_seconds * 1024 * 1024) = Mbps
```

The `CF-Speed-Test` header is required for Cloudflare to accept and process the upload payload.

---

## Anomaly Detection

### Source: `detectAnomalies()` in `frontend/index.html`

Uses z-score analysis on the last 30 latency readings:

```
mean = average(last_30_latencies)
std_dev = standard_deviation(last_30_latencies)
z_score = (value - mean) / std_dev
anomaly = z_score > 2.0
```

Anomalies are displayed as:
- Red dots on the latency chart at the anomaly index
- Flash animation on the latency stat card
- Count and values in a dedicated alert panel

---

## Stability Score Calculation

### Source: `StabilityScore` component (client-side)

Computed from the last 30 history entries:

```
latency_CV = (std_dev(latencies) / mean(latencies)) * 100
jitter_CV  = (std_dev(jitters) / mean(jitters)) * 100
avg_loss   = mean(losses)

stability = 100 - (0.5 * latency_CV + 0.3 * jitter_CV + 0.2 * avg_loss * 10)
stability = clamp(stability, 0, 100)
```

CV (Coefficient of Variation) measures relative variability. A high CV means the metric fluctuates wildly.

| Score | Label |
|---|---|
| 85+ | Rock Solid |
| 65-84 | Stable |
| 40-64 | Fluctuating |
| 0-39 | Unstable |

---

## Network Path Trace

### Source: `TracerouteViz` component (client-side)

Unlike a real traceroute (which sends ICMP/UDP packets with incrementing TTL), the browser-based version pings 7 global endpoints in order:

1. Cloudflare Edge (nearest PoP)
2. Google Edge (nearest PoP)
3. Google DNS (Anycast)
4. Cloudflare DNS (Anycast)
5. AWS CloudFront (CDN)
6. Microsoft CDN
7. Fastly Edge

Each target is pinged 3 times and the median RTT is displayed. This gives a practical view of latency to different parts of the internet from the user's browser.

---

## Packet Loss Pattern Analysis

### Source: `analyzeLossPattern()` in `frontend/index.html`

Examines the loss history array to classify the loss pattern:

- **Burst Loss**: 3+ consecutive samples with packet loss > 0. Indicates hardware issues, cable problems, or WiFi interference.
- **Random Loss**: Isolated loss events separated by healthy samples. Indicates network congestion.
- **Mixed**: Both patterns present.
- **No Loss**: All samples report 0% packet loss.

---

## WiFi Story Generator

### Source: `agent/qoe.py`

A rule-based narrative engine (no AI API dependency) that generates plain-English descriptions:

1. Opens with the current QoE label and score
2. Describes the latency situation with context
3. Comments on jitter stability
4. Notes any packet loss
5. Evaluates app-specific performance
6. Provides actionable recommendations

Example output:
> "Your network is performing well with a QoE score of 82%. Latency is stable at 28ms, which is excellent for all applications. Jitter is minimal at 3ms. No packet loss detected. Video calls and gaming should work smoothly."

---

## Frontend Components

| Component | Props | Description |
|---|---|---|
| `Dashboard` | none | Main container, manages all state and polling |
| `QoEGauge` | score, label | Animated SVG ring gauge |
| `Sparkline` | data, color, w, h | Inline mini trend chart |
| `LiveChart` | history, field, label, color, unit, anomalies | Chart.js line graph |
| `SignalCanvas` | rssi, jitter, packetLoss | Animated waveform canvas |
| `Heatmap` | history | Color-coded latency grid |
| `TracerouteViz` | none | Browser-based network path trace |
| `StabilityScore` | history | Client-side CV calculation |
| `LossPattern` | history | Burst vs random loss analysis |
| `NetworkInfo` | none | IP/ISP/location from ipapi.co |
| `Recommendations` | data | Context-aware tips |
| `SpeedTest` | none | Cloudflare download + upload test |
| `MultiPing` | none | Client-side multi-target ping |
| `PerfTiming` | timing | DNS/TLS/TCP breakdown bars |
| `Timeline` | events | Chronological event log |

---

## Backend API Reference

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/api/ping` | GET | none | `{ latency_ms, timestamp }` |
| `/api/metrics/browser` | POST | `{ latency_ms, jitter_ms, packet_loss_pct, downlink_mbps, ... }` | `{ current, qoe, causes, timing }` |
| `/api/metrics/history` | GET | none | `MetricFrame[]` (last 100) |
| `/api/speedtest/download` | GET | none | Random bytes payload |
| `/api/speedtest/upload` | POST | Binary payload | `{ elapsed_ms, bytes }` |
| `/api/ping/multi` | GET | none | `[{ name, latency_ms }]` |
| `/api/analyze/story` | POST | none | `{ story: string }` |

---

## Browser API Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---|---|---|---|---|
| fetch() timing | Yes | Yes | Yes | Yes |
| navigator.connection | Yes | No | No | Yes |
| PerformanceResourceTiming (cors) | Yes | Yes | Yes | Yes |
| Web Audio API (alerts) | Yes | Yes | Yes | Yes |
| Notification API | Yes | Yes | Yes | Yes |
| localStorage | Yes | Yes | Yes | Yes |

When `navigator.connection` is unavailable (Firefox/Safari), the app:
- Shows "N/A" for connection type and speed class
- Falls back to fetch timing for all latency measurements
- Downlink shows 0 (no browser estimate available)

---

## Data Persistence

### localStorage Keys

| Key | Contents | Max Size |
|---|---|---|
| `netpulse_session` | `{ history[], events[], sampleCount, totalBytes }` | Last 120 history entries, 50 events |
| `netpulse_sessions` | `[{ date, samples, avgLatency, avgQoE }]` | Last 10 saved session snapshots |
| `netpulse_theme` | `"dark"` or `"light"` | Single string |

Data is saved every 5 seconds and restored on page load.

### JSON Export Format

```json
{
  "exported": "2024-01-15T10:30:00.000Z",
  "samples": 142,
  "history": [
    { "latency": 25, "jitter": 3.2, "loss": 0, "throughput": 45, "qoe": 88 }
  ],
  "events": [
    { "time": "10:25:30", "type": "info", "message": "Quality: Moderate > Good (82%)" }
  ],
  "current": { "latency_ms": 25, "jitter_ms": 3.2, "packet_loss_pct": 0, "tx_rate_mbps": 45 },
  "qoe": { "total_score": 88, "label": "Good", "app_profiles": {} }
}
```
