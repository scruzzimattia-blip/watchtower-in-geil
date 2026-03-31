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
    WATCH_LABEL = os.getenv("WATCH_LABEL", "com.watchtower.enable")
    
    # Log-Level (Standard: INFO).
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
