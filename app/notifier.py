import logging
import apprise
from app.config import Config

logger = logging.getLogger(__name__)

class Notifier:
    """
    Diese Klasse nutzt Apprise, um Benachrichtigungen an verschiedenste Dienste zu senden.
    """
    def __init__(self):
        self.apobj = apprise.Apprise()
        urls = Config.NOTIFICATION_URLS
        if urls:
            for url in urls.split(","):
                self.apobj.add(url.strip())
            logger.info(f"Notifier mit {len(self.apobj)} Apprise-URLs initialisiert.")

    def send(self, message, title="Lighthouse Update"):
        """
        Sendet eine einfache Nachricht.
        """
        if not self.apobj:
            logger.debug("Keine Benachrichtigungs-URLs konfiguriert.")
            return

        try:
            self.apobj.notify(body=message, title=title)
        except Exception as e:
            logger.error(f"Fehler beim Senden via Apprise: {e}")

    def send_summary(self, summary):
        """
        Erstellt einen zusammenfassenden Bericht und sendet diesen.
        """
        if summary.is_empty():
            return

        lines = ["📊 **Lighthouse Scan-Zusammenfassung**"]
        if summary.updated:
            lines.append(f"✅ Aktualisiert: {', '.join(summary.updated)}")
        if summary.failed:
            lines.append(f"❌ Fehlgeschlagen: {', '.join(summary.failed)}")
        if summary.rolled_back:
            lines.append(f"⚠️ Rollbacks: {', '.join(summary.rolled_back)}")
        
        self.send("\n".join(lines))

class ScanSummary:
    """
    Sammelt Ergebnisse eines Scan-Durchlaufs.
    """
    def __init__(self):
        self.updated = []
        self.failed = []
        self.rolled_back = []

    def add_updated(self, name):
        self.updated.append(name)

    def add_failed(self, name):
        self.failed.append(name)

    def add_rolled_back(self, name):
        self.rolled_back.append(name)

    def is_empty(self):
        return not (self.updated or self.failed or self.rolled_back)
