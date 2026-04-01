from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.docker_handler import DockerHandler


@pytest.fixture
def handler():
    with patch('aiodocker.Docker'):
        return DockerHandler()

@pytest.mark.asyncio
async def test_run_hook_execution(handler):
    """Prueft, ob Hooks korrekt via exec aufgerufen werden."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/test-hook',
        'Config': {'Labels': {'com.lighthouse.pre-update': 'ls -la'}}
    }

    # Mock exec Objekt
    mock_exec = AsyncMock()

    # Mock stream fuer den async with Block
    mock_stream = AsyncMock()
    mock_stream.read_out.return_value = None

    # Der async with Block ruft start() auf, was ein Objekt liefert,
    # das __aenter__ und __aexit__ hat.
    # mock_exec.start() liefert einen AsyncContextManager
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    mock_exec.start.return_value = mock_context_manager
    container.exec.return_value = mock_exec

    await handler._run_hook(container, 'com.lighthouse.pre-update')

    # Check ob exec mit dem richtigen Befehl gerufen wurde
    args, kwargs = container.exec.call_args
    assert args[0]['Cmd'] == ['ls', '-la']

@pytest.mark.asyncio
async def test_no_hook_if_label_missing(handler):
    """Prueft, dass nichts passiert wenn kein Label vorhanden ist."""
    container = AsyncMock()
    container.show.return_value = {
        'Name': '/no-hook',
        'Config': {'Labels': {}}
    }

    await handler._run_hook(container, 'com.lighthouse.pre-update')
    container.exec.assert_not_called()
