from unittest.mock import MagicMock, patch

import pytest

from app.notifier import Notifier, ScanSummary


@pytest.fixture
def mock_config():
    with patch("app.config.Config.NOTIFICATION_URLS", "discord://webhook_id/webhook_token"):
        yield


def test_send_summary_with_content(mock_config):
    """Prueft, ob eine Zusammenfassung via Apprise gesendet wird."""
    with patch("apprise.Apprise") as mock_apprise_class:
        mock_apobj = MagicMock()
        mock_apprise_class.return_value = mock_apobj

        notifier = Notifier()
        summary = ScanSummary()
        summary.add_updated("app1")
        summary.add_failed("app2")
        summary.add_rolled_back("app3")

        notifier.send_summary(summary)

        # Pruefe, ob notify aufgerufen wurde.
        assert mock_apobj.notify.called
        # Pruefe den Inhalt des Bodys.
        args, kwargs = mock_apobj.notify.call_args
        body = kwargs.get("body", "")
        assert "app1" in body
        assert "app2" in body
        assert "app3" in body
        assert "✅ Aktualisiert" in body
        assert "❌ Fehlgeschlagen" in body
        assert "⚠️ Rollbacks" in body


def test_send_summary_empty(mock_config):
    """Prueft, dass bei einer leeren Zusammenfassung nichts gesendet wird."""
    with patch("apprise.Apprise") as mock_apprise_class:
        mock_apobj = MagicMock()
        mock_apprise_class.return_value = mock_apobj

        notifier = Notifier()
        summary = ScanSummary()

        notifier.send_summary(summary)

        assert not mock_apobj.notify.called


def test_notifier_no_url():
    """Prueft, dass kein Sendeversuch erfolgt, wenn keine URLs konfiguriert sind."""
    with patch("app.config.Config.NOTIFICATION_URLS", ""):
        with patch("apprise.Apprise") as mock_apprise_class:
            mock_apobj = MagicMock()
            mock_apprise_class.return_value = mock_apobj

            notifier = Notifier()
            # Falls apobj leer/leer-initialisiert ist (abhaengig von Impl),
            # sollte notify nicht gerufen werden.
            notifier.send("Test")

            # Da Notifier() apobj immer initialisiert, aber nur URLs addet wenn vorhanden:
            # Wir pruefen ob add gerufen wurde (sollte nicht).
            assert not mock_apobj.add.called
