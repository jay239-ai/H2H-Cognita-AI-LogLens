import subprocess
import re
import time
import os
import sys
from datetime import datetime
import psutil
from agent.normalizer import MetricFrame

# 🚀 Fix for ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_active_interface():
    """Identifies the primary active network interface."""
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    for interface, stat in stats.items():
        if stat.isup and interface in addrs:
            # Skip loopback
            if not any(addr.address.startswith('127.') for addr in addrs[interface]):
                return interface
    return None

def get_throughput(interface, duration=1):
    """Measures real-time throughput by sampling net_io_counters."""
    if not interface: return 0, 0
    
    try:
        io_start = psutil.net_io_counters(pernic=True)[interface]
        time.sleep(duration)
        io_end = psutil.net_io_counters(pernic=True)[interface]
        
        tx_rate = (io_end.bytes_sent - io_start.bytes_sent) * 8 / (1024 * 1024 * duration) # Mbps
        rx_rate = (io_end.bytes_recv - io_start.bytes_recv) * 8 / (1024 * 1024 * duration) # Mbps
        
        return float(tx_rate), float(rx_rate)
    except:
        return 0, 0

def get_nearby_ap_count():
    """Scans for nearby Access Points on the same channel."""
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"], 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )
        # Count occurrences of "BSSID" which represents an AP
        return output.count("BSSID")
    except:
        return 0

def get_windows_wifi_metrics():
    """Parses `netsh wlan show interfaces` for real-time WiFi hardware data."""
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"], 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )
    except subprocess.CalledProcessError:
        return get_ethernet_fallback()

    metrics = {}
    for line in output.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            metrics[key.strip()] = value.strip()

    if not metrics or 'SSID' not in metrics:
        return get_ethernet_fallback()

    # RSSI parsing
    signal_pct = int(metrics.get('Signal', '0').replace('%', ''))
    rssi_dbm = (signal_pct / 2) - 100 
    
    # Real-time throughput sampling
    interface = metrics.get('Description', get_active_interface())
    tx_rate, rx_rate = get_throughput(interface)

    # Ping metrics
    ping_metrics = get_ping_metrics()
    
    # Congestion metric: nearby AP count
    ap_count = get_nearby_ap_count()

    return MetricFrame(
        timestamp=datetime.now(),
        ssid=metrics.get('SSID', 'Unknown'),
        bssid=metrics.get('BSSID', 'Unknown'),
        channel=int(metrics.get('Channel', '0')),
        band=metrics.get('Radio type', 'Unknown'),
        rssi_dbm=int(rssi_dbm),
        noise_floor_dbm=-95,
        snr_db=int(signal_pct / 10),
        tx_rate_mbps=tx_rate,
        rx_rate_mbps=rx_rate,
        latency_ms=ping_metrics['latency'],
        jitter_ms=ping_metrics['jitter'],
        packet_loss_pct=ping_metrics['loss'],
        platform="windows",
        nearby_ap_count=ap_count,
        cpu_usage=psutil.cpu_percent(),
        ram_usage=psutil.virtual_memory().percent
    )

def get_ethernet_fallback():
    """Fallback for Ethernet/Cloud environments."""
    interface = get_active_interface()
    tx_rate, rx_rate = get_throughput(interface)
    ping_metrics = get_ping_metrics()
    
    return MetricFrame(
        timestamp=datetime.now(),
        ssid="Ethernet/Wired",
        bssid="N/A",
        channel=0,
        band="Wired",
        rssi_dbm=-40, # Ideal for wired
        noise_floor_dbm=-110,
        snr_db=70,
        tx_rate_mbps=tx_rate,
        rx_rate_mbps=rx_rate,
        latency_ms=ping_metrics['latency'],
        jitter_ms=ping_metrics['jitter'],
        packet_loss_pct=ping_metrics['loss'],
        platform="windows"
    )

def get_ping_metrics(target="8.8.8.8", count=4):
    """Robust ping parser."""
    try:
        output = subprocess.check_output(
            ["ping", "-n", str(count), target],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        latency_match = re.search(r"Average = (\d+)ms", output)
        loss_match = re.search(r"(\d+)% loss", output)
        min_max = re.findall(r"Minimum = (\d+)ms, Maximum = (\d+)ms", output)
        
        latency = float(latency_match.group(1)) if latency_match else 0
        loss = float(loss_match.group(1)) if loss_match else 100
        jitter = 0
        if min_max:
            min_lat, max_lat = map(float, min_max[0])
            jitter = max_lat - min_lat
            
        return {'latency': latency, 'loss': loss, 'jitter': jitter}
    except:
        return {'latency': 0, 'loss': 100, 'jitter': 0}

if __name__ == "__main__":
    while True:
        metrics = get_windows_wifi_metrics()
        if metrics:
            print(metrics.model_dump_json())
