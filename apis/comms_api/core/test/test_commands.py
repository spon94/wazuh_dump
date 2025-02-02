from unittest.mock import AsyncMock, call, patch
from multiprocessing import Event

import pytest

from comms_api.core.commands import CommandsManager, pull_commands
from wazuh.core.indexer import Indexer
from wazuh.core.indexer.models.commands import Command, Status, Target, TargetType

ORDER_ID = 'UB2jVpEBYSr9jxqDgXAD'
AGENT_ID = '01915801-4b34-7131-9d88-ff06ff05aefd'
COMMAND = Command(order_id=ORDER_ID, status=Status.PENDING, target=Target(id=AGENT_ID, type=TargetType.AGENT))
UPDATED_COMMAND = Command(order_id=ORDER_ID, status=Status.SENT, target=Target(id=AGENT_ID, type=TargetType.AGENT))
INDEXER = Indexer(host='host', user='wazuh', password='wazuh')


@patch('comms_api.core.commands.SyncManager')
def test_commands_manager_initialization(sync_manager_mock):
    """Check that the `CommandsManager.__init___` method works as expected."""
    CommandsManager()

    sync_manager_mock.assert_has_calls([
        call(),
        call().start(),
        call().dict(),
        call().dict(),
    ])


@patch('comms_api.core.commands.SyncManager')
def test_commands_manager_add_commands(sync_manager_mock):
    """Check that the `add_commands` method works as expected."""
    commands_manager = CommandsManager()
    commands_manager._subscriptions = {AGENT_ID: Event()}
    commands_manager._commands = {}
    commands_manager.add_commands([COMMAND])

    assert commands_manager._commands[AGENT_ID] == [COMMAND]


@patch('comms_api.core.commands.SyncManager')
def test_commands_manager_get_commands(sync_manager_mock):
    """Check that the `get_commands` method works as expected."""
    commands_manager = CommandsManager()
    commands_manager._commands = {AGENT_ID: [COMMAND]}
    commands = commands_manager.get_commands(AGENT_ID)

    assert commands == [COMMAND]


@patch('comms_api.core.commands.SyncManager')
def test_commands_manager_get_commands_timeout(sync_manager_mock):
    """Check that the `get_commands` method works as expected if the timeout is reached."""
    commands_manager = CommandsManager()
    commands_manager._subscriptions = {}
    commands_manager._commands = {}
    commands = commands_manager.get_commands(AGENT_ID, 0.01)

    assert commands is None
    assert commands_manager._subscriptions == {}


@patch('comms_api.core.commands.SyncManager')
def test_commands_manager_shutdown(sync_manager_mock):
    """Check that the `shutdown` method works as expected."""
    commands_manager = CommandsManager()
    commands_manager.shutdown()

    sync_manager_mock.assert_has_calls([
        call(),
        call().start(),
        call().dict(),
        call().dict(),
        call().shutdown()
    ])


@pytest.mark.asyncio
@patch('comms_api.core.commands.CommandsManager')
@patch('wazuh.core.indexer.create_indexer', return_value=INDEXER)
@patch('wazuh.core.indexer.commands.CommandsManager.update', new_callable=AsyncMock)
async def test_pull_commands(commands_update_mock, create_indexer_mock, commands_manager_mock):
    commands_manager_mock.get_commands.return_value = [COMMAND]
    commands = await pull_commands(commands_manager_mock, AGENT_ID)

    assert commands == [UPDATED_COMMAND]
    create_indexer_mock.assert_called_once()
    commands_update_mock.assert_called_once_with([UPDATED_COMMAND])
