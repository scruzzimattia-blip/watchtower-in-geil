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

    def check_and_update(self, container):
        """
        Prueft, ob ein neues Image fuer den Container verfuegbar ist.
        Falls ja, wird der Container mit dem neuen Image neu gestartet.
        """
        image_name = container.image.tags[0] if container.image.tags else None
        if not image_name:
            logger.warning(f"Container {container.name} hat keine Tags. Ueberspringe.")
            return

        try:
            logger.info(f"Pulle neustes Image fuer {image_name}...")
            # Pulle das Image, um zu sehen, ob es ein Update gibt.
            new_image = self.client.images.pull(image_name)
            
            # Vergleiche die IDs des aktuellen Images und des neu gepullten Images.
            if new_image.id != container.image.id:
                logger.info(f"Update verfuegbar fuer {container.name}! Starte neu...")
                self.recreate_container(container, image_name)
            else:
                logger.info(f"Container {container.name} ist bereits auf dem neusten Stand.")
                
        except Exception as e:
            logger.error(f"Fehler beim Update von {container.name}: {e}")

    def recreate_container(self, container, image_name):
        """
        Stoppt, entfernt und startet den Container neu mit dem neuen Image.
        Dabei werden wichtige Konfigurationen (Ports, Volumes, Envs) beibehalten.
        """
        # Extrahiere Konfiguration des alten Containers.
        config = container.attrs['Config']
        host_config = container.attrs['HostConfig']
        
        # Stoppen und Entfernen.
        logger.info(f"Stoppe Container {container.name}...")
        container.stop()
        logger.info(f"Entferne Container {container.name}...")
        container.remove()
        
        # Neu erstellen mit derselben Konfiguration.
        # Hinweis: Hier koennten noch mehr Parameter uebernommen werden (z.B. Netzwerke).
        new_container = self.client.containers.run(
            image=image_name,
            name=container.name,
            detach=True,
            environment=config.get('Env', []),
            ports=host_config.get('PortBindings', {}),
            volumes=host_config.get('Binds', []),
            restart_policy=host_config.get('RestartPolicy', {"Name": "always"}),
            labels=config.get('Labels', {})
        )
        logger.info(f"Container {new_container.name} erfolgreich mit neuem Image gestartet.")

    def close(self):
        """
        Schliesst die Verbindung zum Docker-Client.
        """
        self.client.close()
        logger.info("Docker-Client-Verbindung wurde ordnungsgemaess geschlossen.")
