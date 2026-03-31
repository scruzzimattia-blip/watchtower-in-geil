import requests
import logging
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
        Sendet eine Nachricht an den konfigurierten Webhook.
        """
        if not self.webhook_url:
            logger.debug("Keine Webhook-URL konfiguriert. Benachrichtigung wird uebersprungen.")
            return

        try:
            payload = {"content": message}
            # Falls es ein Slack-Webhook ist, koennte das Feld 'text' statt 'content' sein.
            # Wir versuchen es erst mit 'content' (Discord Standard).
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            # Falls 400er Fehler, versuchen wir Slack-Format.
            if response.status_code == 400:
                payload = {"text": message}
                response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code < 300:
                logger.info("Benachrichtigung erfolgreich gesendet.")
            else:
                logger.warning(f"Fehler beim Senden der Benachrichtigung: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Senden der Benachrichtigung: {e}")
