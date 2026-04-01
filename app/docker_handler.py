import aiodocker
import logging
import asyncio
import time
from app.config import Config
from app.notifier import Notifier
from app import metrics

logger = logging.getLogger(__name__)

class DockerHandler:
    """
    Diese Klasse uebernimmt die asynchrone Kommunikation mit der Docker-API.
    """
    def __init__(self):
        try:
            # Verbindungsdaten fuer Remote Docker Hosts vorbereiten.
            conn_args = {}
            if Config.DOCKER_HOST:
                conn_args['url'] = Config.DOCKER_HOST
            
            self.client = aiodocker.Docker(**conn_args)
            self.notifier = Notifier()
            logger.info("Verbindung zur Docker-API (aiodocker) erfolgreich hergestellt.")
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zur Docker-API: {e}")
            raise

    async def get_watchable_containers(self):
        """
        Gibt eine Liste aller Container zurueck, die ueberwacht werden sollen.
        Die Liste ist nach Abhaengigkeiten sortiert.
        """
        all_containers = await self.client.containers.list()
        watch_label = Config.WATCH_LABEL
        
        watchable = []
        container_map = {} # Name -> Container Object

        for container in all_containers:
            info = await container.show()
            container_name = info['Name'].lstrip('/')
            container_map[container_name] = container
            
            labels = info.get('Config', {}).get('Labels', {})

            # Filterlogik (Include/Exclude).
            if Config.INCLUDE_CONTAINERS and container_name not in Config.INCLUDE_CONTAINERS:
                continue
            if Config.EXCLUDE_CONTAINERS and container_name in Config.EXCLUDE_CONTAINERS:
                continue

            if not watch_label:
                watchable.append(container)
            elif watch_label in labels and labels[watch_label].lower() == "true":
                watchable.append(container)
        
        # Sortierung nach Abhaengigkeiten.
        sorted_watchable = await self.sort_containers_by_dependencies(watchable, container_map)
        
        logger.info(f"Es wurden {len(sorted_watchable)} zu ueberwachende Container gefunden.")
        return sorted_watchable

    async def sort_containers_by_dependencies(self, containers, container_map):
        """
        Sortiert Container topologisch basierend auf 'depends_on' Labels.
        """
        from collections import deque

        # Graphen aufbauen.
        adj = {info['Name'].lstrip('/'): [] for info in [await c.show() for c in containers]}
        in_degree = {name: 0 for name in adj}
        
        # Nur Container beruecksichtigen, die wir auch ueberwachen.
        watchable_names = set(adj.keys())

        for container in containers:
            info = await container.show()
            name = info['Name'].lstrip('/')
            labels = info.get('Config', {}).get('Labels', {})
            
            # Docker Compose nutzt oft 'com.docker.compose.depends_on'
            depends_raw = labels.get('com.docker.compose.depends_on', '')
            # Format ist oft "service:condition", wir brauchen nur den Namen.
            dependencies = [d.split(':')[0] for d in depends_raw.split(',') if d]

            for dep in dependencies:
                if dep in watchable_names:
                    adj[dep].append(name)
                    in_degree[name] += 1

        # Topologische Sortierung (Kahn's Algorithmus).
        queue = deque([name for name in in_degree if in_degree[name] == 0])
        sorted_names = []

        while queue:
            u = queue.popleft()
            sorted_names.append(u)
            for v in adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Falls ein Zyklus existiert, nehmen wir die verbliebenen einfach dazu.
        for name in watchable_names:
            if name not in sorted_names:
                sorted_names.append(name)

        # Zurueck zu Container-Objekten.
        name_to_container = { (await c.show())['Name'].lstrip('/'): c for c in containers }
        return [name_to_container[name] for name in sorted_names if name in name_to_container]

    async def check_and_update(self, container, summary=None):
        """
        Prueft auf Updates und fuehrt diese asynchron aus.
        """
        info = await container.show()
        container_name = info['Name'].lstrip('/')
        image_name = info['Config']['Image']
        
        image_info = await self.client.images.inspect(image_name)
        old_image_id = image_info['Id']

        try:
            logger.info(f"Pulle neustes Image fuer {image_name}...")
            
            auth = None
            if Config.REGISTRY_USER and Config.REGISTRY_PASS:
                auth = {'username': Config.REGISTRY_USER, 'password': Config.REGISTRY_PASS}

            await self.client.images.pull(image_name, auth=auth)
            new_image_info = await self.client.images.inspect(image_name)
            new_image_id = new_image_info['Id']

            if new_image_id != old_image_id:
                msg = f"Update verfuegbar fuer {container_name} ({image_name})!"
                logger.info(msg)
                
                if Config.DRY_RUN:
                    logger.info(f"[DRY RUN] Neustart von {container_name} wird uebersprungen.")
                    if summary:
                        summary.add_updated(f"{container_name} (simuliert)")
                    return

                # Starte den Container neu mit Rollback-Sicherung.
                success = await self.recreate_with_rollback(container, image_name, summary)
                if success:
                    await self.cleanup_old_image(old_image_id)
                    metrics.UPDATES_TOTAL.inc()
                else:
                    metrics.UPDATES_FAILED.inc()
            else:
                logger.info(f"Container {container_name} ist bereits aktuell.")
                
        except Exception as e:
            error_msg = f"Fehler beim Update von {container_name}: {e}"
            logger.error(error_msg)
            metrics.UPDATES_FAILED.inc()
            if summary:
                summary.add_failed(container_name)
            if not Config.SKIP_PULL_ERROR:
                raise

    async def _run_hook(self, container, label_key):
        """Fuehrt einen Befehl innerhalb des Containers aus (Lifecycle Hook)."""
        info = await container.show()
        labels = info.get('Config', {}).get('Labels', {})
        hook_cmd = labels.get(label_key)

        if not hook_cmd:
            return

        logger.info(f"Fuehre Hook aus ({label_key}) fuer {info['Name']}: {hook_cmd}")
        try:
            # aiodocker exec nutzen.
            config = {
                "Cmd": hook_cmd.split(),
                "AttachStdout": True,
                "AttachStderr": True
            }
            exec_obj = await container.exec(config)
            async with exec_obj.start() as stream:
                output = await stream.read_out()
                if output:
                    logger.debug(f"Hook Output: {output.data.decode().strip()}")
        except Exception as e:
            logger.error(f"Fehler beim Ausfuehren des Hooks {label_key}: {e}")

    async def recreate_with_rollback(self, container, image_name, summary):
        """
        Implementiert den sicheren Rollback-Mechanismus und Lifecycle Hooks.
        """
        info = await container.show()
        original_name = info['Name'].lstrip('/')
        backup_name = f"{original_name}_backup"

        # Pre-Update Hook ausfuehren.
        await self._run_hook(container, "com.lighthouse.pre-update")

        # 1. Backup erstellen (Umbenennen).
        logger.info(f"Erstelle Backup: Benenne {original_name} in {backup_name} um...")
        try:
            await container.rename(backup_name)
        except Exception as e:
            logger.error(f"Konnte Backup fuer {original_name} nicht erstellen: {e}")
            if summary:
                summary.add_failed(original_name)
            return False

        # 2. Neuen Container erstellen.
        logger.info(f"Starte neuen Container {original_name}...")
        new_container = None
        try:
            config = self._prepare_config(info, image_name, original_name)
            new_container = await self.client.containers.create(config=config, name=original_name)
            await self._connect_networks(new_container, info)
            await new_container.start()
            
            # 3. Validieren (Healthcheck).
            if await self.wait_for_health(new_container):
                logger.info(f"Container {original_name} erfolgreich aktualisiert.")
                if summary:
                    summary.add_updated(original_name)
                
                # Post-Update Hook ausfuehren.
                await self._run_hook(new_container, "com.lighthouse.post-update")

                # Altes Backup loeschen.
                backup_container = await self.client.containers.get(backup_name)
                await backup_container.stop()
                await backup_container.delete()
                return True
            else:
                raise RuntimeError("Healthcheck fehlgeschlagen.")

        except Exception as e:
            logger.warning(f"Update fehlgeschlagen für {original_name}: {e}. Starte Rollback...")
            metrics.ROLLBACKS_TOTAL.inc()
            if summary:
                summary.add_rolled_back(original_name)
            
            if new_container:
                try:
                    await new_container.stop()
                    await new_container.delete()
                except Exception:
                    pass

            try:
                backup_container = await self.client.containers.get(backup_name)
                await backup_container.rename(original_name)
                await backup_container.start()
                logger.info(f"Rollback fuer {original_name} erfolgreich abgeschlossen.")
            except Exception as re:
                logger.critical(f"KRITISCH: Rollback fuer {original_name} fehlgeschlagen: {re}")
            
            return False

    def _prepare_config(self, info, image_name, name):
        """Extrahiert und bereitet die Konfiguration fuer den neuen Container vor."""
        old_config = info['Config']
        host_config = info['HostConfig']
        
        new_config = {
            'Image': image_name,
            'Labels': old_config.get('Labels', {}),
            'Env': old_config.get('Env', []),
            'Entrypoint': old_config.get('Entrypoint'),
            'Cmd': old_config.get('Cmd'),
            'User': old_config.get('User'),
            'WorkingDir': old_config.get('WorkingDir'),
            'HostConfig': {
                'PortBindings': host_config.get('PortBindings', {}),
                'Binds': host_config.get('Binds', []),
                'RestartPolicy': host_config.get('RestartPolicy', {"Name": "always"}),
                'LogConfig': host_config.get('LogConfig', {}),
                'ExtraHosts': host_config.get('ExtraHosts', []),
            }
        }
        return new_config

    async def _connect_networks(self, container, old_info):
        """Verbindet den neuen Container mit den Netzwerken des alten."""
        networks = old_info.get('NetworkSettings', {}).get('Networks', {})
        for net_name, net_config in networks.items():
            try:
                if net_name == 'bridge':
                    continue 
                
                network = await self.client.networks.get(net_name)
                await network.connect({
                    'Container': container.id,
                    'EndpointConfig': {
                        'Aliases': net_config.get('Aliases', [])
                    }
                })
            except Exception as e:
                logger.debug(f"Netzwerk-Verbindung zu {net_name} fehlgeschlagen: {e}")

    async def wait_for_health(self, container, timeout=60):
        """Wartet darauf, dass ein Container 'healthy' wird."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            info = await container.show()
            state = info.get('State', {})
            status = state.get('Status')
            health = state.get('Health', {}).get('Status')
            
            if status != 'running':
                return False
            
            if health == 'healthy' or health is None:
                return True
            
            if health == 'unhealthy':
                return False
                
            await asyncio.sleep(2)
        return False

    async def cleanup_old_image(self, image_id):
        """Entfernt ein altes Image."""
        try:
            await self.client.images.delete(image_id)
            logger.info(f"Altes Image {image_id[:12]} bereinigt.")
        except Exception:
            pass

    async def close(self):
        """Schliesst den Client."""
        await self.client.close()

    async def listen_events(self):
        """Horcht auf Docker-Events."""
        logger.info("Starte Docker Event-Listener...")
        try:
            async for event in self.client.events():
                if event['Type'] == 'container' and event['Action'] == 'start':
                    container_id = event['Actor']['Attributes'].get('name') or event['id']
                    logger.info(f"Event: Container {container_id} gestartet. Pruefe auf Updates...")
        except Exception as e:
            logger.error(f"Fehler im Event-Listener: {e}")
