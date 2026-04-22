import subprocess
import re
import time
import os
import sys
from datetime import datetime
import psutil

# 🚀 Fix for ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.normalizer import MetricFrame

def get_active_interface():
    """Identifies the primary active network interface."""
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    for interface, stat in stats.items():
        if stat.isup and interface in addrs:
            if not any(addr.address.startswith('127.') for addr in addrs[interface]):
                return interface
    return None

def get_throughput(interface, duration=1):
    """Measures real-time throughput."""
    if not interface: return 0, 0
    try:
        io_start = psutil.net_io_counters(pernic=True)[interface]
        time.sleep(duration)
        io_end = psutil.net_io_counters(pernic=True)[interface]
        tx_rate = (io_end.bytes_sent - io_start.bytes_sent) * 8 / (1024 * 1024 * duration)
        rx_rate = (io_end.bytes_recv - io_start.bytes_recv) * 8 / (1024 * 1024 * duration)
        return float(tx_rate), float(rx_rate)
    except:
        return 0, 0

def get_linux_network_metrics():
    """Hardware-aware Linux collector using nmcli and psutil."""
    ssid, bssid, channel, freq, signal = "Ethernet/Cloud", "N/A", 0, "N/A", 100
    
    # Try nmcli for WiFi specific data
    try:
        nmcli_out = subprocess.check_output(
            ["nmcli", "-t", "-f", "active,ssid,bssid,chan,freq,signal", "dev", "wifi"], 
            universal_newlines=True
        )
        for line in nmcli_out.split('\n'):
            if line.startswith('yes:'):
                parts = line.split(':')
                if len(parts) >= 6:
                    _, ssid, bssid, channel, freq, signal = parts
                    break
    except:
        pass

    rssi_dbm = (int(signal) / 2) - 100 if str(signal).isdigit() else -50
    interface = get_active_interface()
    tx_rate, rx_rate = get_throughput(interface)
    ping_metrics = get_ping_metrics()

    return MetricFrame(
        timestamp=datetime.now(),
        ssid=ssid,
        bssid=bssid,
        channel=int(channel) if str(channel).isdigit() else 0,
        band=f"{freq} MHz" if freq != "N/A" else "Ethernet",
        rssi_dbm=int(rssi_dbm),
        noise_floor_dbm=-100,
        snr_db=int((int(signal) if str(signal).isdigit() else 100) / 2),
        tx_rate_mbps=tx_rate,
        rx_rate_mbps=rx_rate,
        latency_ms=ping_metrics['latency'],
        jitter_ms=ping_metrics['jitter'],
        packet_loss_pct=ping_metrics['loss'],
        platform="linux",
        cpu_usage=psutil.cpu_percent(),
        ram_usage=psutil.virtual_memory().percent
    )

def get_ping_metrics(target="8.8.8.8", count=4):
    """Linux ping parser."""
    try:
        output = subprocess.check_output(
            ["ping", "-c", str(count), target],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        loss_match = re.search(r"(\d+)% packet loss", output)
        rtt_match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/([\d\.]+)", output)
        
        return {
            'latency': float(rtt_match.group(1)) if rtt_match else 0,
            'jitter': float(rtt_match.group(2)) if rtt_match else 0,
            'loss': float(loss_match.group(1)) if loss_match else 0
        }
    except:
        return {'latency': 0, 'jitter': 0, 'loss': 100}

if __name__ == "__main__":
    while True:
        metrics = get_linux_network_metrics()
        if metrics:
            print(metrics.model_dump_json())
        time.sleep(1)
