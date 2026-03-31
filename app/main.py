import time
import logging
import sys
from app.config import Config
from app.docker_handler import DockerHandler

# Logger einrichten mit "ss" statt "ß".
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """
    Der Haupteinstiegspunkt des Watchtower-Klons.
    Hier wird die Endlosschleife gestartet, die regelmaessig
    nach Updates sucht und diese ausfuehrt.
    """
    logger.info("Watchtower-Klon gestartet. Druecke Strg+C zum Schliessen.")
    logger.info(f"Abfrageintervall: {Config.POLL_INTERVAL} Sekunden.")
    
    # Docker-Handler initialisieren.
    try:
        handler = DockerHandler()
    except Exception as e:
        logger.error(f"Kritischer Fehler beim Starten des Docker-Handlers: {e}")
        sys.exit(1)

    try:
        while True:
            logger.info("Starte Pruefung auf neue Image-Versionen...")
            
            # Liste der zu ueberwachenden Container abrufen.
            containers = handler.get_watchable_containers()
            for container in containers:
                logger.info(f"Pruefe Container: {container.name} (Image: {container.image.tags})")
                # TODO: Phase 3 - Update-Pruefung und Neustart implementieren.
            
            logger.info(f"Warten auf den naechsten Durchlauf in {Config.POLL_INTERVAL}s.")
            time.sleep(Config.POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Beenden durch Benutzer... Auf Wiedersehen!")
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        handler.close()

if __name__ == "__main__":
    main()
