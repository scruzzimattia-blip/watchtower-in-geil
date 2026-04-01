import pytest
from unittest.mock import AsyncMock, patch
from app.docker_handler import DockerHandler
from app.config import Config

@pytest.fixture
def handler():
    with patch('aiodocker.Docker'):
        return DockerHandler()

@pytest.mark.asyncio
async def test_dependency_sorting(handler):
    """Testet die korrekte Sortierung von Containern basierend auf depends_on."""
    
    # Mock Container
    c_db = AsyncMock()
    c_db.show.return_value = {
        'Name': '/database',
        'Config': {'Labels': {}}
    }
    
    c_app = AsyncMock()
    c_app.show.return_value = {
        'Name': '/application',
        'Config': {'Labels': {'com.docker.compose.depends_on': 'database:service_healthy'}}
    }
    
    containers = [c_app, c_db]
    
    sorted_containers = await handler.sort_containers_by_dependencies(containers)
    
    # Namen extrahieren
    sorted_names = [(await c.show())['Name'].lstrip('/') for c in sorted_containers]
    
    # DB muss vor App kommen
    assert sorted_names == ['database', 'application']

@pytest.mark.asyncio
async def test_include_exclude_filter(handler):
    """Testet die Namens-basierten Filter (Include/Exclude)."""
    
    c1 = AsyncMock()
    c1.show.return_value = {'Name': '/web-server', 'Config': {'Labels': {Config.WATCH_LABEL: "true"}}}
    
    c2 = AsyncMock()
    c2.show.return_value = {'Name': '/db-server', 'Config': {'Labels': {Config.WATCH_LABEL: "true"}}}
    
    handler.client.containers.list = AsyncMock(return_value=[c1, c2])
    
    # Test Include
    with patch('app.config.Config.INCLUDE_CONTAINERS', ['web-server']):
        watchable = await handler.get_watchable_containers()
        assert len(watchable) == 1
        assert (await watchable[0].show())['Name'] == '/web-server'
        
    # Test Exclude
    with patch('app.config.Config.EXCLUDE_CONTAINERS', ['web-server']):
        with patch('app.config.Config.INCLUDE_CONTAINERS', []):
            watchable = await handler.get_watchable_containers()
            assert len(watchable) == 1
            assert (await watchable[0].show())['Name'] == '/db-server'
