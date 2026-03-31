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
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))
    
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
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
    
    # Authentifizierungsdaten fuer private Registries (optional).
    REGISTRY_USER = os.getenv("REGISTRY_USER")
    REGISTRY_PASS = os.getenv("REGISTRY_PASS")
