import logging

from prometheus_client import Counter, Gauge, start_http_server

from app.config import Config

logger = logging.getLogger(__name__)

# Metriken definieren.
UPDATES_TOTAL = Counter('lighthouse_updates_total', 'Gesamtzahl der erfolgreichen Updates')
UPDATES_FAILED = Counter('lighthouse_updates_failed', 'Gesamtzahl der fehlgeschlagenen Updates')
ROLLBACKS_TOTAL = Counter('lighthouse_rollbacks_total', 'Gesamtzahl der durchgefuehrten Rollbacks')
LAST_SCAN_TIME = Gauge(
    "lighthouse_last_scan_time_seconds", "Zeitstempel des letzten Scans (Unix Epoch)"
)

def start_metrics_server():
    """Startet den Prometheus Metrik-Server."""
    try:
        start_http_server(Config.METRICS_PORT)
        logger.info(f"Prometheus Metrik-Server auf Port {Config.METRICS_PORT} gestartet.")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Metrik-Servers: {e}")
