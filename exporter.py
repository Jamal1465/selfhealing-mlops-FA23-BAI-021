
import time
import requests
from prometheus_client import start_http_server, Gauge

# ── Metric definition (name MUST match exactly) ──────────────────────────────
CONFIDENCE_GAUGE = Gauge(
    'prediction_confidence_score',
    'Latest prediction confidence score from the ML Sentiment API'
)

# ── Target: app running via Minikube NodePort ─────────────────────────────────

APP_URL = "http://172.193.26.41:32500/api/latest-confidence"

POLL_INTERVAL = 5   # seconds
DEFAULT_VALUE  = 1.0


def fetch_confidence() -> float:
    """Return the latest confidence score, or 1.0 on any error."""
    try:
        resp = requests.get(APP_URL, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("confidence", DEFAULT_VALUE))
    except Exception as e:
        print(f"[exporter] Could not reach app: {e}  — using default {DEFAULT_VALUE}")
        return DEFAULT_VALUE


if __name__ == "__main__":
    start_http_server(8000)
    print("[exporter] Serving metrics on :8000  —  polling app every 5 s ...")
    while True:
        confidence = fetch_confidence()
        CONFIDENCE_GAUGE.set(confidence)
        print(f"[exporter] prediction_confidence_score = {confidence:.4f}")
        time.sleep(POLL_INTERVAL)
