import time
import logging
import sys
import signal
from app.config import Config
from app.docker_handler import DockerHandler

# Logger einrichten mit "ss" statt "ß".
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Globale Variable fuer die Steuerung der Hauptschleife.
RUNNING = True

def signal_handler(sig, frame):
    """
    Handler fuer Signale wie SIGTERM oder SIGINT.
    Setzt RUNNING auf False, um die Schleife sauber zu beenden.
    """
    global RUNNING
    logger.info(f"Signal {sig} empfangen. Beende Anwendung sauber...")
    RUNNING = False

def get_version():
    """Liest die Version aus der VERSION-Datei im Hauptverzeichnis."""
    try:
        with open("VERSION", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unbekannt"

def main():
    """
    Der Haupteinstiegspunkt des Watchtower-Klons.
    Hier wird die Endlosschleife gestartet, die regelmaessig
    nach Updates sucht und diese ausfuehrt.
    """
    # Signal-Handler registrieren.
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    version = get_version()
    logger.info(f"Watchtower-Klon (v{version}) gestartet. Druecke Strg+C zum Schliessen.")
    logger.info(f"Abfrageintervall: {Config.POLL_INTERVAL} Sekunden.")
    
    # Docker-Handler initialisieren.
    try:
        handler = DockerHandler()
    except Exception as e:
        logger.error(f"Kritischer Fehler beim Starten des Docker-Handlers: {e}")
        sys.exit(1)

    try:
        while RUNNING:
            logger.info("Starte Pruefung auf neue Image-Versionen...")
            
            # Liste der zu ueberwachenden Container abrufen.
            containers = handler.get_watchable_containers()
            for container in containers:
                if not RUNNING:
                    break
                logger.info(f"Pruefe Container: {container.name} (Image: {container.image.tags})")
                handler.check_and_update(container)
            
            if RUNNING:
                logger.info(f"Warten auf den naechsten Durchlauf in {Config.POLL_INTERVAL}s.")
                # Wir schlafen in kleinen Schritten (1s), um schneller auf Signale reagieren zu koennen.
                for _ in range(Config.POLL_INTERVAL):
                    if not RUNNING:
                        break
                    time.sleep(1)
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        handler.close()
        logger.info("Anwendung ordnungsgemaess beendet.")

if __name__ == "__main__":
    main()
