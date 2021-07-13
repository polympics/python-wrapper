"""Dataclasses to represent the various types returned by the API."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from dataclasses_json import DataClassJsonMixin, config, dataclass_json


__all__ = (
    'Account',
    'AccountTeamUpdateEvent',
    'App',
    'AppCredentials',
    'Award',
    'Callback',
    'ClientError',
    'Credentials',
    'DataError',
    'EventType',
    'Permissions',
    'PolympicsError',
    'ServerError',
    'Session',
    'SignupsStatus',
    'Team'
)


@dataclass
class Permissions:
    """Permissions, returned as bit flags by the API."""

    manage_permissions: bool = False
    manage_account_teams: bool = False
    manage_account_details: bool = False
    manage_teams: bool = False
    authenticate_users: bool = False
    manage_own_team: bool = False
    manage_awards: bool = False

    @classmethod
    def from_int(cls, value: int) -> Permissions:
        """Parse permissions from a series of bit flags."""
        values = []
        for n in range(6):
            values.append(bool(value & (1 << n)))
        return cls(*values)

    @property
    def values(self) -> list[bool]:
        """Get the permissions as a list of bools."""
        return [
            self.manage_permissions,
            self.manage_account_teams,
            self.manage_account_details,
            self.manage_teams,
            self.authenticate_users,
            self.manage_own_team,
            self.manage_awards
        ]

    def to_int(self) -> int:
        """Turn the permissions into a series of bit flags."""
        value = 0
        for n, permission in enumerate(self.values):
            value |= permission << n
        return value

    def __lt__(self, other: Permissions) -> bool:
        """Check if these permissions are a strict subset of another."""
        differ = False
        for ours, theirs in zip(self.values, other.value):
            if ours and not theirs:
                return False
            if theirs and not ours:
                differ = True
        return differ

    def __lte__(self, other: Permissions) -> bool:
        """Check if these permissions are a subset or the same as another."""
        return any(
            ours and not theirs
            for ours, theirs in zip(self.values, other.value)
        )

    def __gt__(self, other: Permissions) -> bool:
        """Check if these permissions are a strict superset of another."""
        return other < self

    def __gte__(self, other: Permissions) -> bool:
        """Check if these permissions are a superset or the same as others."""
        return other <= self

    def __eq__(self, other: Permissions) -> bool:
        """Check if these permissions are the same as others."""
        return all(
            ours == theirs
            for ours, theirs in zip(self.values, other.value)
        )

    def __or__(self, other: Permissions) -> Permissions:
        """Add other permissions to these."""
        return Permissions.from_int(self.to_int() | other.to_int())

    __add__ = __or__

    def __invert__(self) -> Permissions:
        """Get the opposite of these permissions."""
        return Permissions.from_int(~self.to_int())

    def __and__(self, other: Permissions) -> Permissions:
        """Get all permissions specified in both this and other."""
        return Permissions.from_int(self.to_int() & other.to_int())

    def __sub__(self, other: Permissions) -> Permissions:
        """Get all permissions specified in this but not other."""
        return Permissions.from_int(self.to_int() & (~other.to_int()))


@dataclass_json
@dataclass
class Team:
    """A team returned by the API."""

    id: int
    name: str
    created_at: datetime
    member_count: int
    awards: list[Award]


@dataclass
class Account(DataClassJsonMixin):
    """An account returned by the API."""

    id: int
    name: str
    discriminator: str
    created_at: datetime
    permissions: Permissions = field(metadata=config(
        encoder=Permissions.to_int,
        decoder=Permissions.from_int
    ))
    awards: list[Award]
    avatar_url: Optional[str] = None
    team: Optional[Team] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """Ensure the Discord ID is an int."""
        account = super().from_dict(data)
        account.id = int(account.id)
        return account


@dataclass_json
@dataclass
class Award:
    """An award returned by the API."""

    id: int
    title: str
    image_url: str
    # Will be present for Client.get_award but no other time.
    awardees: Optional[list[Account]] = None
    # As above but may still be None if the award is not for a team.
    team: Optional[Team] = None


@dataclass_json
@dataclass
class SignupsStatus:
    """Whether or not signups are open."""

    signups_open: bool


class EventType(enum.Enum):
    """An event type for a callback."""

    ACCOUNT_TEAM_UPDATE = 'account_team_update'


@dataclass_json
@dataclass
class Callback:
    """A callback returned by the API."""

    id: int
    url: str
    event: EventType = field(metadata=config(
        encoder=lambda ev: ev.value,
        decoder=EventType
    ))


@dataclass_json
@dataclass
class AccountTeamUpdateEvent:
    """An event for when an account's team is changed."""

    account: Account
    team: Optional[Team]


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
class App:
    """Metadata for an app."""

    username: str
    name: str


@dataclass_json
@dataclass
class AppCredentials(Credentials, App):
    """Credentials and data for an app."""


@dataclass
class PolympicsError(Exception):
    """An error returned by the API."""

    code: int

    def __str__(self) -> str:
        """Show this error as a string."""
        return f'Polympics error: {self.code}'


class ServerError(PolympicsError):
    """An error on the server-side."""

    def __str__(self) -> str:
        """Show this error as a string."""
        return f'{self.code}: Internal server error'


@dataclass
class DataError(PolympicsError):
    """An error present in the data passed to the server."""

    issues: list[dict[str, Any]]

    def __str__(self) -> str:
        """Show this error as a string."""
        lines = [f'{self.code}: {len(self.issues)} data validation error/s:']
        for issue in self.issues:
            lines.append('  {path}: {msg} ({type})'.format(
                path=' -> '.join(issue['loc']),
                msg=issue['msg'], type=issue['type']
            ))
        return '\n'.join(lines)


@dataclass
class ClientError(PolympicsError):
    """A different client-resolvable error."""

    detail: str

    def __str__(self) -> str:
        """Show this error as a string."""
        return f'{self.code}: {self.detail}'
