import pytest
from unittest.mock import MagicMock, patch
from app.notifier import Notifier
from app.config import Config

@pytest.fixture
def mock_requests_post():
    """Mockt requests.post, um Netzwerkaufrufe zu vermeiden."""
    with patch('requests.post') as mock_post:
        yield mock_post

def test_notifier_send_no_url(mock_requests_post):
    """Prueft, dass nichts gesendet wird, wenn keine URL konfiguriert ist."""
    with patch('app.config.Config.WEBHOOK_URL', None):
        notifier = Notifier()
        notifier.send("Test-Nachricht")
        mock_requests_post.assert_not_called()

def test_notifier_send_success(mock_requests_post):
    """Prueft, ob eine Nachricht erfolgreich an den Webhook gesendet wird."""
    mock_requests_post.return_value.status_code = 204
    
    with patch('app.config.Config.WEBHOOK_URL', "http://fake-webhook.com"):
        notifier = Notifier()
        notifier.send("Test-Nachricht")
        
        # Pruefe, ob requests.post mit dem richtigen Payload aufgerufen wurde.
        mock_requests_post.assert_called_once()
        args, kwargs = mock_requests_post.call_args
        assert kwargs['json']['content'] == "Test-Nachricht"

def test_notifier_slack_fallback(mock_requests_post):
    """Prueft den Fallback auf das Slack-Format (text statt content)."""
    # Erster Aufruf (Discord) schlaegt mit 400 fehl, zweiter Aufruf (Slack) ist erfolgreich.
    mock_requests_post.side_effect = [
        MagicMock(status_code=400, text="Bad Request"),
        MagicMock(status_code=200, text="ok")
    ]
    
    with patch('app.config.Config.WEBHOOK_URL', "http://fake-webhook.com"):
        notifier = Notifier()
        notifier.send("Test-Nachricht")
        
        assert mock_requests_post.call_count == 2
        # Zweiter Aufruf sollte 'text' als Key haben.
        _, kwargs = mock_requests_post.call_args
        assert kwargs['json']['text'] == "Test-Nachricht"
