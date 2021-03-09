"""Utils for making requests to the API."""
from typing import Any, Optional

import aiohttp

from .pagination import Paginator
from .types import (
    Account, App, AppCredentials, ClientError, Credentials, DataError,
    Permissions, ServerError, Session, Team
)


__all__ = ('UnauthenticatedClient', 'AppClient', 'UserClient')


class UnauthenticatedClient:
    """A client for making un-, user- or app-authenitcated requests."""

    def __init__(
            self, credentials: Optional[Credentials] = None,
            base_url: str = 'http://127.0.0.1:8000'):
        """Set up the client."""
        if credentials:
            self.auth = aiohttp.BasicAuth(
                credentials.username, credentials.password
            )
        else:
            self.auth = None
        self.client = None
        self.base_url = base_url

    async def get_client(self) -> aiohttp.ClientSession:
        """Get the aiohttp client session, or create one."""
        if (not self.client) or self.client.closed:
            self.client = aiohttp.ClientSession(auth=self.auth)
        return self.client

    async def handle_response(
            self, response: aiohttp.ClientResponse,
            data_type: Any = None) -> dict[str, Any]:
        """Process a response from the API."""
        if response.status == 500:
            raise ServerError(500)
        if response.status == 204:
            return {}
        data = await response.json()
        if response.ok:
            if data_type:
                return data_type.from_dict(data)
            return data
        elif response.status == 422:
            raise DataError(422, data['detail'])
        else:
            raise ClientError(response.status, data['detail'])

    async def request(
            self, method: str, path: str, response_type: Any = None,
            **kwargs: dict[str, Any]) -> Any:
        """Make a request to the API."""
        client = await self.get_client()
        url = f'{self.base_url}{path}'
        async with client.request(method, url, **kwargs) as resp:
            return await self.handle_response(resp, response_type)

    async def get_account(self, discord_id: int) -> Account:
        """Get an account by Discord ID."""
        return await self.request('GET', f'/account/{discord_id}', Account)

    async def get_team(self, team_id: int) -> Team:
        """Get a team by ID."""
        return await self.request('GET', f'/team/{team_id}', Team)

    def list_accounts(
            self, search: Optional[str] = None,
            team: Optional[Team] = None) -> Paginator:
        """Get a paginator of accounts matching a query."""
        params = {}
        if search:
            params['q'] = search
        if team:
            params['team'] = team.id
        return Paginator(
            method='GET',
            path='/accounts/search',
            client=self,
            params=params,
            data_type=Account
        )

    def list_teams(self, search: str = None) -> Paginator:
        """Get a paginator of teams, optionally with a search query."""
        params = {}
        if search:
            params['q'] = search
        return Paginator(
            method='GET',
            path='/teams/search',
            client=self,
            params=params,
            data_type=Team
        )

    async def close(self):
        """Close the connection."""
        await self.client.close()


class AuthenticatedClient(UnauthenticatedClient):
    """Client that adds endpoints only available when authenticated."""

    async def create_account(
            self, discord_id: int, display_name: str, discriminator: int,
            avatar_url: Optional[str] = None, team: Optional[Team] = None,
            permissions: Optional[Permissions] = None) -> Account:
        """Create a new account."""
        return await self.request('POST', '/accounts/signup', json={
            'discord_id': discord_id,
            'display_name': display_name,
            'discriminator': discriminator,
            'avatar_url': avatar_url,
            'team': team.id if team else None,
            'permissions': permissions.to_int() if permissions else 0
        }, response_type=Account)

    async def update_account(
            self, account: Account, display_name: str = None,
            discriminator: int = None, avatar_url: str = None,
            team: Team = None, grant_permissions: Permissions = None,
            revoke_permissions: Permissions = None):
        """Edit an account."""
        data = {}
        if display_name:
            account.display_name = display_name
            data['display_name'] = display_name
        if discriminator:
            account.discriminator = discriminator
            data['discriminator'] = discriminator
        if avatar_url:
            account.avatar_url = avatar_url
            data['avatar_url'] = avatar_url
        if team:
            account.team = team
            data['team'] = team.id
        if grant_permissions:
            account.permissions += grant_permissions
            data['grant_permissions'] = grant_permissions.to_int()
        if revoke_permissions:
            account.permissions -= revoke_permissions
        await self.request(
            'PATCH', f'/account/{account.discord_id}', json=data
        )

    async def delete_account(self, account: Account):
        """Delete an account."""
        await self.request('DELETE', f'/account/{account.discord_id}')

    async def create_team(self, name: str) -> Team:
        """Create a new team."""
        return await self.request('POST', '/teams/new', json={
            'name': name
        }, response_type=Team)

    async def update_team(self, team: Team, name: str):
        """Edit a team's name."""
        team.name = name
        await self.request('PATCH', f'/team/{team.id}', json={'name': name})

    async def delete_team(self, team: Team):
        """Delete a team."""
        await self.request('DELETE', f'/team/{team.id}')


class AppClient(AuthenticatedClient):
    """Client that adds endpoints only available to apps."""

    async def create_session(self, account: Account) -> Session:
        """Create a user authentication session."""
        return await self.request(
            'POST', f'/account/{account.discord_id}/session', Session
        )

    async def reset_token(self) -> AppCredentials:
        """Reset the authenticated app's token."""
        app = await self.request('POST', '/app/reset_token', AppCredentials)
        self.auth = aiohttp.BasicAuth(app.username, app.password)
        await self.client.close()
        return app

    async def get_app(self) -> App:
        """Get metadata on the authenticated app."""
        return await self.request('GET', '/app', App)


class UserClient(AuthenticatedClient):
    """Client that adds endpoints only available to users."""

    async def get_self(self) -> Account:
        """Get the account our credentials authenticate us for.

        Errors if using no credentials or app credentials.
        """
        return await self.request('GET', '/accounts/me', Account)
