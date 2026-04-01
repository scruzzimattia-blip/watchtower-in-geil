import logging

import requests

from app.config import Config

logger = logging.getLogger(__name__)

class Notifier:
    """
    Diese Klasse uebernimmt das Senden von Benachrichtigungen ueber Webhooks.
    """
    def __init__(self):
        self.webhook_url = Config.WEBHOOK_URL

    def send(self, message):
        """
        Sendet eine einfache Nachricht.
        """
        self._post(message)

    def send_summary(self, summary):
        """
        Erstellt einen schoen formatierten Bericht aus einem ScanSummary-Objekt
        und sendet diesen.
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

        if len(lines) > 1:
            self._post("\n".join(lines))

    def _post(self, message):
        """
        Interne Hilfsmethode fuer den POST-Request.
        """
        if not self.webhook_url:
            logger.debug("Keine Webhook-URL konfiguriert. Benachrichtigung wird uebersprungen.")
            return

        try:
            payload = {"content": message}
            response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code == 400:
                payload = {"text": message}
                response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code < 300:
                logger.info("Benachrichtigung erfolgreich gesendet.")
            else:
                logger.warning(f"Fehler beim Senden der Benachrichtigung: {response.status_code}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Senden: {e}")

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
