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
            old_image_id = container.image.id
            new_image = self.client.images.pull(image_name)
            
            # Vergleiche die IDs des aktuellen Images und des neu gepullten Images.
            if new_image.id != old_image_id:
                logger.info(f"Update verfuegbar fuer {container.name}! Starte neu...")
                self.recreate_container(container, image_name)
                
                # Altes Image entfernen, falls es keine Tags mehr hat (dangling).
                self.cleanup_old_image(old_image_id)
            else:
                logger.info(f"Container {container.name} ist bereits auf dem neusten Stand.")
                
        except Exception as e:
            logger.error(f"Fehler beim Update von {container.name}: {e}")

    def cleanup_old_image(self, image_id):
        """
        Entfernt ein altes Image, falls es nicht mehr verwendet wird (dangling).
        """
        try:
            # Wir versuchen das Image zu entfernen. Falls es noch von anderen
            # Containern genutzt wird, wird Docker einen Fehler werfen, den wir abfangen.
            self.client.images.remove(image=image_id, noprune=False)
            logger.info(f"Altes Image {image_id[:12]} wurde erfolgreich bereinigt.")
        except Exception:
            # Ignorieren, falls das Image noch in Benutzung ist.
            pass

    def recreate_container(self, container, image_name):
        """
        Stoppt, entfernt und startet den Container neu mit dem neuen Image.
        Versucht so viele Konfigurationsparameter wie moeglich zu uebernehmen.
        """
        # Extrahiere Konfiguration des alten Containers.
        attrs = container.attrs
        config = attrs['Config']
        host_config = attrs['HostConfig']
        
        # Vorbereitung der Parameter fuer den neuen Container.
        # Wir versuchen, moeglichst viele Details zu erhalten.
        run_kwargs = {
            'image': image_name,
            'name': container.name,
            'detach': True,
            'environment': config.get('Env', []),
            'ports': host_config.get('PortBindings', {}),
            'volumes': host_config.get('Binds', []),
            'restart_policy': host_config.get('RestartPolicy', {"Name": "always"}),
            'labels': config.get('Labels', {}),
            'entrypoint': config.get('Entrypoint'),
            'command': config.get('Cmd'),
            'user': config.get('User'),
            'working_dir': config.get('WorkingDir'),
            'hostname': config.get('Hostname'),
            'domainname': config.get('Domainname'),
            'mac_address': config.get('MacAddress'),
        }

        # Netzwerke extrahieren.
        networks = attrs.get('NetworkSettings', {}).get('Networks', {})
        network_names = list(networks.keys())
        
        # Stoppen und Entfernen des alten Containers.
        logger.info(f"Stoppe Container {container.name}...")
        try:
            container.stop(timeout=10)
            logger.info(f"Entferne Container {container.name}...")
            container.remove()
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Containers {container.name}: {e}")
            return

        # Neu erstellen.
        try:
            # Den neuen Container mit dem ersten Netzwerk starten.
            if network_names:
                run_kwargs['network'] = network_names[0]
            
            new_container = self.client.containers.run(**run_kwargs)
            
            # Weitere Netzwerke verbinden, falls vorhanden.
            if len(network_names) > 1:
                for net_name in network_names[1:]:
                    network = self.client.networks.get(net_name)
                    network.connect(new_container)
            
            logger.info(f"Container {new_container.name} erfolgreich mit neuem Image gestartet.")
        except Exception as e:
            logger.error(f"Kritischer Fehler beim Neustart von {container.name}: {e}")
            logger.error("Der Container konnte nicht wiederhergestellt werden!")

    def close(self):
        """
        Schliesst die Verbindung zum Docker-Client.
        """
        self.client.close()
        logger.info("Docker-Client-Verbindung wurde ordnungsgemaess geschlossen.")
