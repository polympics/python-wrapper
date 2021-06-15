"""Handlers for event callbacks.

Note that this does not implement an actual HTTP server, rather it provides
utility functions for such an implementation. It also does not validate
secrets.
"""
from typing import Any

from .types import AccountTeamUpdateEvent


__all__ = ('account_team_update',)


def account_team_update(data: dict[str, Any]) -> AccountTeamUpdateEvent:
    """Parse an account team update event."""
    return AccountTeamUpdateEvent.from_dict(data)
