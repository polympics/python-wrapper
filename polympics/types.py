"""Dataclasses to represent the various types returned by the API."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from dataclasses_json import config, dataclass_json


__all__ = (
    'Account', 'App', 'Credentials', 'Permissions', 'PolympicsError',
    'Session', 'Team'
)


@dataclass
class Permissions:
    """Permissions, returned as bit flags by the API."""

    manage_permissions: bool
    manage_account_teams: bool
    manage_account_details: bool
    manage_teams: bool
    authenticate_users: bool
    manage_own_team: bool

    @classmethod
    def from_int(cls, value: int) -> Permissions:
        """Parse permissions from a series of bit flags."""
        values = []
        for n in range(6):
            values.append(value & (1 << n))
        return cls(*values)

    def to_int(self) -> int:
        """Turn the permissions into a series of bit flags."""
        permissions = [
            self.manage_permissions,
            self.manage_account_teams,
            self.manage_account_details,
            self.manage_teams,
            self.authenticate_users,
            self.manage_own_team
        ]
        value = 0
        for n, permission in enumerate(permissions):
            value |= permission << n
        return value


@dataclass_json
@dataclass
class Team:
    """A team returned by the API."""

    id: int
    name: str
    created_at: datetime
    member_count: int

    client: Any


@dataclass_json
@dataclass
class Account:
    """An account returned by the API."""

    discord_id: int
    display_name: str
    team: Team
    permissions: Permissions = field(metadata=config(
        encoder=Permissions.to_int,
        decoder=Permissions.from_int
    ))
    created_at: datetime


@dataclass_json
@dataclass
class PaginatedResponse:
    """A paginated list of objects returned by the API."""

    page: int
    per_page: int
    pages: int
    results: int
    data: list[dict[str, Any]]

    def parse_as(self, data_type: Any) -> list[Any]:
        """Attempt to parse the data as some JSON dataclass."""
        values = []
        for record in self.data:
            values.append(data_type.from_dict(record))
        return values

    @property
    def accounts(self) -> list[Account]:
        """Attempt to parse the data as a list of accounts."""
        return self.parse_as(Account)

    @property
    def teams(self) -> list[Team]:
        """Attempt to parse the data as a list of teams."""
        return self.parse_as(Team)


@dataclass
class Credentials:
    """Credentials for a user session or app."""

    username: str
    password: str


@dataclass_json
@dataclass
class Session(Credentials):
    """Credentials and data for a user auth session."""

    expires_at: datetime


@dataclass_json
@dataclass
class App(Credentials):
    """Credentials and data for an app."""

    display_name: str
    expires_at: datetime


@dataclass
class PolympicsError(Exception):
    """An error returned by the API."""

    code: int
    detail: str

    def __str__(self) -> str:
        """Show this error as a string."""
        return f'{self.code}: {self.detail}'
