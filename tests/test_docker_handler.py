import pytest
from unittest.mock import MagicMock, patch
from app.docker_handler import DockerHandler
from app.config import Config

@pytest.fixture
def mock_docker_client():
    """Mockt den Docker-Client, um API-Aufrufe zu simulieren."""
    with patch('docker.from_env') as mock_env:
        client = MagicMock()
        mock_env.return_value = client
        yield client

def test_get_watchable_containers(mock_docker_client):
    """Testet, ob nur Container mit dem richtigen Label zurueckgegeben werden."""
    # Erstelle Test-Container.
    container1 = MagicMock()
    container1.name = "watch-me"
    container1.labels = {Config.WATCH_LABEL: "true"}
    
    container2 = MagicMock()
    container2.name = "ignore-me"
    container2.labels = {Config.WATCH_LABEL: "false"}
    
    container3 = MagicMock()
    container3.name = "no-label"
    container3.labels = {}
    
    mock_docker_client.containers.list.return_value = [container1, container2, container3]
    
    handler = DockerHandler()
    watchable = handler.get_watchable_containers()
    
    assert len(watchable) == 1
    assert watchable[0].name == "watch-me"

def test_check_and_update_no_change(mock_docker_client):
    """Prueft, dass kein Neustart erfolgt, wenn das Image identisch ist."""
    container = MagicMock()
    container.name = "test-container"
    container.image.id = "sha256:old_id"
    container.image.tags = ["nginx:latest"]
    
    new_image = MagicMock()
    new_image.id = "sha256:old_id"
    
    mock_docker_client.images.pull.return_value = new_image
    
    handler = DockerHandler()
    # Mocking recreate_container, um sicherzustellen, dass es NICHT aufgerufen wird.
    handler.recreate_container = MagicMock()
    handler.cleanup_old_image = MagicMock()
    
    handler.check_and_update(container)
    
    handler.recreate_container.assert_not_called()
    handler.cleanup_old_image.assert_not_called()
