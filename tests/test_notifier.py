from unittest.mock import patch

import pytest

from app.notifier import Notifier, ScanSummary


@pytest.fixture
def mock_config():
    with patch('app.config.Config.WEBHOOK_URL', 'http://webhook.url'):
        yield

def test_send_summary_with_content(mock_config):
    """Prueft, ob eine Zusammenfassung mit Inhalt gesendet wird."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200

        notifier = Notifier()
        summary = ScanSummary()
        summary.add_updated("app1")
        summary.add_failed("app2")
        summary.add_rolled_back("app3")

        notifier.send_summary(summary)

        assert mock_post.called
        # Pruefe, ob alle Elemente im Payload vorkommen.
        payload = mock_post.call_args[1]['json']['content']
        assert "app1" in payload
        assert "app2" in payload
        assert "app3" in payload
        assert "✅ Aktualisiert" in payload
        assert "❌ Fehlgeschlagen" in payload
        assert "⚠️ Rollbacks" in payload

def test_send_summary_empty(mock_config):
    """Prueft, dass bei einer leeren Zusammenfassung nichts gesendet wird."""
    with patch('requests.post') as mock_post:
        notifier = Notifier()
        summary = ScanSummary()

        notifier.send_summary(summary)

        assert not mock_post.called

def test_notifier_no_url():
    """Prueft, dass kein Fehler auftritt, wenn kein Webhook konfiguriert ist."""
    with patch('app.config.Config.WEBHOOK_URL', None):
        notifier = Notifier()
        # Sollte einfach lautlos ueberspringen.
        notifier.send("Test")
