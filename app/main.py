import asyncio
import logging
import signal
import sys
from datetime import datetime

from croniter import croniter

from app.config import Config
from app.docker_handler import DockerHandler
from app.metrics import LAST_SCAN_TIME, start_metrics_server
from app.notifier import ScanSummary

# Logger einrichten.
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Globale Variable fuer die Steuerung der Hauptschleife.
RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    logger.info(f"Signal {sig} empfangen. Beende Anwendung sauber...")
    RUNNING = False

def get_version():
    try:
        with open("VERSION", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unbekannt"

async def get_next_run_delay():
    """Berechnet die Verzögerung bis zum nächsten Durchlauf (Cron oder Interval)."""
    if Config.CRON_SCHEDULE:
        now = datetime.now()
        cron = croniter(Config.CRON_SCHEDULE, now)
        next_run = cron.get_next(datetime)
        delay = (next_run - now).total_seconds()
        logger.info(f"Naechster Cron-Durchlauf geplant fuer: {next_run} (in {int(delay)}s)")
        return delay
    return Config.POLL_INTERVAL

async def main():
    # Signal-Handler (async-kompatibel).
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    version = get_version()
    logger.info(f"Lighthouse (v{version}) gestartet.")

    # Metrik-Server starten.
    start_metrics_server()

    handler = DockerHandler()

    # Event-Listener im Hintergrund starten.
    event_task = asyncio.create_task(handler.listen_events())

    try:
        while RUNNING:
            logger.info("Starte Scan-Durchlauf...")
            LAST_SCAN_TIME.set_to_current_time()
            summary = ScanSummary()

            containers = await handler.get_watchable_containers()

            # Parallele Ausfuehrung der Pruefungen.
            tasks = [handler.check_and_update(c, summary) for c in containers]
            await asyncio.gather(*tasks)

            # Zusammenfassung senden.
            handler.notifier.send_summary(summary)

            if RUNNING:
                delay = await get_next_run_delay()
                # Schlafen in kleinen Schritten, um auf RUNNING=False zu reagieren.
                for _ in range(int(delay)):
                    if not RUNNING:
                        break
                    await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        event_task.cancel()
        await handler.close()
        logger.info("Anwendung ordnungsgemaess beendet.")

async def shutdown():
    global RUNNING
    RUNNING = False
    logger.info("Shutdown eingeleitet...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
