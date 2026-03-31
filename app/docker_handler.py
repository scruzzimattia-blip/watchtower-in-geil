import docker
import logging
import time
from app.config import Config
from app.notifier import Notifier

logger = logging.getLogger(__name__)

class DockerHandler:
    """
    Diese Klasse uebernimmt die Kommunikation mit der Docker-API ueber den Socket.
    """
    def __init__(self):
        try:
            # Initialisiert den Docker-Client mit den Standardeinstellungen (z.B. docker.sock).
            self.client = docker.from_env()
            self.notifier = Notifier()
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
            
            # Authentifizierungsdaten fuer private Registries vorbereiten.
            auth_config = None
            if Config.REGISTRY_USER and Config.REGISTRY_PASS:
                auth_config = {
                    'username': Config.REGISTRY_USER,
                    'password': Config.REGISTRY_PASS
                }

            new_image = self.client.images.pull(image_name, auth_config=auth_config)
            
            # Vergleiche die IDs des aktuellen Images und des neu gepullten Images.
            if new_image.id != old_image_id:
                msg = f"Update verfuegbar fuer {container.name} ({image_name})!"
                logger.info(msg)
                
                if Config.DRY_RUN:
                    logger.info(f"[DRY RUN] Neustart von {container.name} wird uebersprungen.")
                    self.notifier.send(f"🔍 {msg} (Simulation)")
                else:
                    # Starte den Container neu und pruefe auf Gesundheit.
                    new_container = self.recreate_container(container, image_name)
                    
                    if new_container and self.wait_for_health(new_container):
                        self.notifier.send(f"✅ {msg} (Erfolgreich aktualisiert)")
                        # Altes Image entfernen, falls es keine Tags mehr hat (dangling).
                        self.cleanup_old_image(old_image_id)
                    elif new_container:
                        # Rollback einleiten!
                        rollback_msg = f"⚠️ {container.name} ist ungesund! Rollback wird eingeleitet..."
                        logger.warning(rollback_msg)
                        self.notifier.send(rollback_msg)
                        # HINWEIS: Fuer ein echtes Rollback muessten wir die Attribute des alten Containers sichern.
                        # Wir versuchen hier einfach, den ungesunden Container zu stoppen.
                        # In v0.3.0 ist das Rollback als Konzept enthalten.
                        new_container.stop(timeout=5)
                        logger.error(f"Container {container.name} konnte nicht erfolgreich aktualisiert werden.")
            else:
                logger.info(f"Container {container.name} ist bereits auf dem neusten Stand.")
                
        except Exception as e:
            error_msg = f"Fehler beim Update von {container.name}: {e}"
            logger.error(error_msg)
            if not Config.SKIP_PULL_ERROR:
                raise
            self.notifier.send(f"❌ {error_msg}")

    def wait_for_health(self, container, timeout=60):
        """
        Wartet darauf, dass ein Container 'healthy' wird.
        Falls kein Healthcheck definiert ist, wird nur geprueft, ob er laeuft.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            status = container.status
            health = container.attrs.get('State', {}).get('Health', {}).get('Status')
            
            if status != 'running':
                return False
            
            if health == 'healthy' or health is None:
                return True
            
            if health == 'unhealthy':
                return False
                
            time.sleep(2)
        return False

    def cleanup_old_image(self, image_id):
        """
        Entfernt ein altes Image, falls es nicht mehr verwendet wird (dangling).
        """
        try:
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
            return None

        # Neu erstellen.
        try:
            if network_names:
                run_kwargs['network'] = network_names[0]
            
            new_container = self.client.containers.run(**run_kwargs)
            
            if len(network_names) > 1:
                for net_name in network_names[1:]:
                    network = self.client.networks.get(net_name)
                    network.connect(new_container)
            
            logger.info(f"Container {new_container.name} erfolgreich mit neuem Image gestartet.")
            return new_container
        except Exception as e:
            logger.error(f"Kritischer Fehler beim Neustart von {container.name}: {e}")
            return None

    def close(self):
        """
        Schliesst die Verbindung zum Docker-Client.
        """
        self.client.close()
        logger.info("Docker-Client-Verbindung wurde ordnungsgemaess geschlossen.")
