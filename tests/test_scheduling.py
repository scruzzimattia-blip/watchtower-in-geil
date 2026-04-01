import pytest
from datetime import datetime
from unittest.mock import patch
from app.main import get_next_run_delay
from app.config import Config

@pytest.mark.asyncio
async def test_scheduling_interval():
    """Prueft, ob bei fehlendem Cron das Standardintervall genutzt wird."""
    with patch('app.config.Config.CRON_SCHEDULE', None):
        delay = await get_next_run_delay()
        assert delay == float(Config.POLL_INTERVAL)

@pytest.mark.asyncio
async def test_scheduling_cron():
    """Prueft, ob Cron-Ausdruecke korrekt in Sekunden umgerechnet werden."""
    # Alle 5 Minuten.
    with patch('app.config.Config.CRON_SCHEDULE', '*/5 * * * *'):
        # 12:00:00 Uhr
        fixed_now = datetime(2026, 4, 1, 12, 0, 0)
        # Naechster Lauf muss 12:05:00 sein -> 300s Differenz
        delay = await get_next_run_delay(now=fixed_now)
        assert delay == 300.0

@pytest.mark.asyncio
async def test_scheduling_cron_daily():
    """Prueft einen taeglichen Cron-Job."""
    # Jeden Tag um 03:00 Uhr morgens.
    with patch('app.config.Config.CRON_SCHEDULE', '0 3 * * *'):
        # Es ist 02:00:00 Uhr nachts.
        fixed_now = datetime(2026, 4, 1, 2, 0, 0)
        # Naechster Lauf in 1 Stunde (3600s)
        delay = await get_next_run_delay(now=fixed_now)
        assert delay == 3600.0
