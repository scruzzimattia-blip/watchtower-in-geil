import docker
import logging
from app.config import Config

logger = logging.getLogger(__name__)

class DockerHandler:
    """
    Diese Klasse uebernimmt die Kommunikation mit der Docker-API ueber den Socket.
    """
    def __init__(self):
        try:
            # Initialisiert den Docker-Client mit den Standardeinstellungen (z.B. docker.sock).
            self.client = docker.from_env()
            logger.info("Verbindung zur Docker-API erfolgreich hergestellt.")
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zur Docker-API: {e}")
            raise

    def get_watchable_containers(self):
        """
        Gibt eine Liste aller Container zurueck, die ueberwacht werden sollen.
        Falls WATCH_LABEL konfiguriert ist, werden nur Container mit diesem Label geprueft.
        """
        all_containers = self.client.containers.list()
        watch_label = Config.WATCH_LABEL
        
        if not watch_label:
            logger.info("Kein Label konfiguriert. Ueberwache alle laufenden Container.")
            return all_containers
        
        watchable = []
        for container in all_containers:
            # Pruefung, ob das Label gesetzt ist und den Wert 'true' hat.
            labels = container.labels
            if watch_label in labels and labels[watch_label].lower() == "true":
                watchable.append(container)
        
        logger.info(f"Es wurden {len(watchable)} zu ueberwachende Container gefunden.")
        return watchable

    def close(self):
        """
        Schliesst die Verbindung zum Docker-Client.
        """
        self.client.close()
        logger.info("Docker-Client-Verbindung wurde ordnungsgemaess geschlossen.")
