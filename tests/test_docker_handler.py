import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.docker_handler import DockerHandler
from app.config import Config
from app.notifier import ScanSummary

@pytest.fixture
def mock_aiodocker():
    """Mockt den aiodocker.Docker Client."""
    with patch('aiodocker.Docker') as mock_env:
        client = AsyncMock()
        mock_env.return_value = client
        yield client

@pytest.mark.asyncio
async def test_get_watchable_containers_async(mock_aiodocker):
    """Testet, ob nur Container mit dem richtigen Label zurueckgegeben werden."""
    container1 = AsyncMock()
    container1.show.return_value = {
        'Config': {'Labels': {Config.WATCH_LABEL: "true"}},
        'Name': '/watch-me'
    }
    
    container2 = AsyncMock()
    container2.show.return_value = {
        'Config': {'Labels': {Config.WATCH_LABEL: "false"}},
        'Name': '/ignore-me'
    }
    
    mock_aiodocker.containers.list.return_value = [container1, container2]
    
    handler = DockerHandler()
    watchable = await handler.get_watchable_containers()
    
    assert len(watchable) == 1

@pytest.mark.asyncio
async def test_check_and_update_no_change_async(mock_aiodocker):
    """Prueft, dass kein Neustart erfolgt, wenn das Image identisch ist."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/test-container',
        'Config': {'Image': 'nginx:latest'}
    }
    
    mock_aiodocker.images.inspect.side_effect = [
        {'Id': 'sha256:old_id'}, # Erster Aufruf (vor pull)
        {'Id': 'sha256:old_id'}  # Zweiter Aufruf (nach pull)
    ]
    
    handler = DockerHandler()
    handler.recreate_with_rollback = AsyncMock()
    
    await handler.check_and_update(container)
    
    handler.recreate_with_rollback.assert_not_called()

@pytest.mark.asyncio
async def test_rollback_on_failure(mock_aiodocker):
    """Testet den Rollback-Mechanismus bei einem fehlgeschlagenen Healthcheck."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/test-app',
        'Config': {'Image': 'nginx:latest', 'Labels': {}},
        'HostConfig': {}
    }
    
    handler = DockerHandler()
    # Mock wait_for_health, um ein Scheitern zu simulieren.
    handler.wait_for_health = AsyncMock(return_value=False)
    
    # Mock create, rename, start etc.
    new_container = AsyncMock()
    mock_aiodocker.containers.create.return_value = new_container
    
    backup_container = AsyncMock()
    mock_aiodocker.containers.get.return_value = backup_container

    summary = ScanSummary()
    success = await handler.recreate_with_rollback(container, 'nginx:latest', summary)
    
    assert success is False
    assert len(summary.rolled_back) == 1
    # Sicherstellen, dass das Backup zurueck-umbenannt und gestartet wurde.
    backup_container.rename.assert_called_with('test-app')
    backup_container.start.assert_called()
