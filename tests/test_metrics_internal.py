from unittest.mock import AsyncMock, patch

import pytest

from app import metrics
from app.docker_handler import DockerHandler


@pytest.fixture
def handler():
    with patch('aiodocker.Docker'):
        return DockerHandler()

@pytest.mark.asyncio
async def test_metrics_increment_on_success(handler):
    """Prueft, ob Metriken bei Erfolg hochgezaehlt werden."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/success-app',
        'Config': {'Image': 'nginx:latest'}
    }

    # Mock images
    handler.client.images.inspect = AsyncMock(side_effect=[
        {'Id': 'old'}, {'Id': 'new'}
    ])
    handler.client.images.pull = AsyncMock()

    # Mock recreate
    handler.recreate_with_rollback = AsyncMock(return_value=True)
    handler.cleanup_old_image = AsyncMock()

    # Aktuelle Werte
    before = metrics.UPDATES_TOTAL._value.get()

    await handler.check_and_update(container)

    assert metrics.UPDATES_TOTAL._value.get() == before + 1

@pytest.mark.asyncio
async def test_metrics_increment_on_rollback(handler):
    """Prueft, ob Rollback-Metriken hochgezaehlt werden."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/fail-app',
        'Config': {'Image': 'nginx:latest', 'Labels': {}},
        'HostConfig': {}
    }

    # Simulation eines Fehlers in der Unterfunktion
    handler._create_and_start_container = AsyncMock(side_effect=RuntimeError("Boom"))
    handler.client.containers.get = AsyncMock() # backup container

    # Aktuelle Werte
    before = metrics.ROLLBACKS_TOTAL._value.get()

    await handler.recreate_with_rollback(container, 'nginx:latest', None)

    assert metrics.ROLLBACKS_TOTAL._value.get() == before + 1
