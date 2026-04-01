import os

from dotenv import load_dotenv

# Lade Umgebungsvariablen aus einer .env Datei, falls vorhanden.
load_dotenv()

class Config:
    """
    Konfigurationseinstellungen fuer das Tool.
    Alle Werte koennen ueber Umgebungsvariablen angepasst werden.
    """
    # Abfrageintervall in Sekunden (Standard: 300 Sekunden / 5 Minuten).
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))

    # Label, nach dem gesucht werden soll, um Container zu ueberwachen.
    # Falls leer, werden alle Container geprueft.
    WATCH_LABEL = os.getenv("WATCH_LABEL", "com.lighthouse.enable")

    # Log-Level (Standard: INFO).
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # URL fuer Benachrichtigungen (z.B. Discord/Slack Webhook).
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # Falls True, werden keine Aenderungen an Containern vorgenommen.
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

    # Falls True, wird bei einem Pull-Fehler der naechste Container geprueft.
    SKIP_PULL_ERROR = os.getenv("SKIP_PULL_ERROR", "false").lower() == "true"

    # Maximale Anzahl an parallelen Worker-Threads (Standard: 4).
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    # Cron-Ausdruck fuer die Planung (optional, z.B. "0 3 * * *").
    CRON_SCHEDULE = os.getenv("CRON_SCHEDULE")

    # Apprise-URLs fuer Benachrichtigungen (kommagetrennt).
    NOTIFICATION_URLS = os.getenv("NOTIFICATION_URLS", "")

    # Prometheus Metriken Port.
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8080"))

    # Filter fuer Container Namen/IDs (kommagetrennt).
    INCLUDE_CONTAINERS = os.getenv("INCLUDE_CONTAINERS", "").split(",") if os.getenv("INCLUDE_CONTAINERS") else []
    EXCLUDE_CONTAINERS = os.getenv("EXCLUDE_CONTAINERS", "").split(",") if os.getenv("EXCLUDE_CONTAINERS") else []

    # Remote Docker Konfiguration.
    DOCKER_HOST = os.getenv("DOCKER_HOST")
    DOCKER_CERT_PATH = os.getenv("DOCKER_CERT_PATH")
    DOCKER_TLS_VERIFY = os.getenv("DOCKER_TLS_VERIFY", "false").lower() == "true"

    # Authentifizierungsdaten fuer private Registries (optional).
    REGISTRY_USER = os.getenv("REGISTRY_USER")
    REGISTRY_PASS = os.getenv("REGISTRY_PASS")
