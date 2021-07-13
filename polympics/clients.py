"""Utils for making requests to the API."""
from typing import Any, Optional

import aiohttp

from .pagination import Paginator
from .types import (
    Account,
    App,
    AppCredentials,
    Award,
    Callback,
    ClientError,
    Credentials,
    DataError,
    EventType,
    Permissions,
    ServerError,
    Session,
    SignupsStatus,
    Team
)


__all__ = ('UnauthenticatedClient', 'AppClient', 'UserClient', 'NO_TEAM')

NO_TEAM = object()


class UnauthenticatedClient:
    """A client for making un-, user- or app-authenticated requests."""

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
            self,
            response: aiohttp.ClientResponse,
            data_type: Any = dict) -> Any:
        """Process a response from the API."""
        if response.status == 500:
            raise ServerError(500)
        if response.status == 204:
            return None
        if response.ok and not data_type:
            return
        data = await response.json()
        if response.ok:
            if data_type == dict:
                return data
            return data_type.from_dict(data)
        elif response.status == 422:
            raise DataError(422, data['detail'])
        else:
            raise ClientError(response.status, data['detail'])

    async def request(
            self,
            method: str,
            path: str,
            response_type: Any = dict,
            **kwargs: dict[str, Any]) -> Any:
        """Make a request to the API."""
        client = await self.get_client()
        url = f'{self.base_url}{path}'
        async with client.request(method, url, **kwargs) as resp:
            return await self.handle_response(resp, response_type)

    async def get_account(self, id: int) -> Account:
        """Get an account by Discord ID."""
        return await self.request('GET', f'/account/{id}', Account)

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

    async def discord_authenticate(self, token: str) -> Session:
        """Create a session from a Discord user token."""
        return await self.request('POST', '/auth/discord', Session, json={
            'token': token
        })

    async def close(self):
        """Close the connection."""
        await self.client.close()

    async def update_account(
            self,
            account: Account,
            name: str = None,
            discriminator: int = None,
            avatar_url: str = None,
            team: Team = None,
            grant_permissions: Permissions = None,
            revoke_permissions: Permissions = None,
            discord_token: str = None) -> Account:
        """Edit an account."""
        data = {}
        if name:
            data['name'] = name
        if discriminator:
            data['discriminator'] = discriminator
        if avatar_url:
            data['avatar_url'] = avatar_url
        if team:
            if team == NO_TEAM:
                data['team'] = 0
            else:
                data['team'] = team.id
        if grant_permissions:
            data['grant_permissions'] = grant_permissions.to_int()
        if revoke_permissions:
            data['revoke_permissions'] = revoke_permissions.to_int()
        if discord_token:
            data['discord_token'] = discord_token
        return await self.request(
            'PATCH', f'/account/{account.id}', json=data,
            response_type=Account
        )

    async def get_award(self, award_id: int) -> Award:
        """Get an award by ID."""
        data = await self.request('GET', f'/award/{award_id}')
        award = Award.from_dict(data['award'])
        award.awardees = [Account.from_dict(raw) for raw in data['awardees']]
        award.team = Team.from_dict(data['team']) if data['team'] else None
        return award

    async def check_signups(self) -> bool:
        """Check if signups are currently open."""
        data = await self.request('GET', '/accounts/signups', SignupsStatus)
        return data['signups_open']


class AuthenticatedClient(UnauthenticatedClient):
    """Client that adds endpoints only available when authenticated.

    Does not implement /auth/reset_token or /auth/me, as the return type of
    these vary by the type of authentication used.
    """

    async def create_account(
            self,
            id: int,
            name: str,
            discriminator: int,
            avatar_url: Optional[str] = None,
            team: Optional[Team] = None,
            permissions: Optional[Permissions] = None) -> Account:
        """Create a new account."""
        return await self.request('POST', '/accounts/new', json={
            'id': id,
            'name': name,
            'discriminator': discriminator,
            'avatar_url': avatar_url,
            'team': team.id if team else None,
            'permissions': permissions.to_int() if permissions else 0
        }, response_type=Account)

    async def delete_account(self, account: Account):
        """Delete an account."""
        await self.request('DELETE', f'/account/{account.id}')

    async def create_team(self, name: str) -> Team:
        """Create a new team."""
        return await self.request('POST', '/teams/new', json={
            'name': name
        }, response_type=Team)

    async def update_team(self, team: Team, name: str) -> Team:
        """Edit a team's name."""
        return await self.request(
            'PATCH', f'/team/{team.id}', json={'name': name},
            response_type=Team
        )

    async def delete_team(self, team: Team):
        """Delete a team."""
        await self.request('DELETE', f'/team/{team.id}')

    async def create_award(
            self,
            title: str,
            image_url: str,
            team: Team,
            accounts: list[Account]) -> Award:
        """Create a new award."""
        return await self.request('POST', '/awards/new', Award, json={
            'title': title,
            'image_url': image_url,
            'team': team.id,
            'accounts': [account.id for account in accounts]
        })

    async def update_award(
            self,
            award: Award,
            *,
            title: Optional[str] = None,
            image_url: Optional[str] = None,
            team: Optional[Team] = None) -> Award:
        """Edit an award."""
        return await self.request('PATCH', f'/award/{award.id}', Award, json={
            'title': title,
            'image_url': image_url,
            'team': team.id if team else None
        })

    async def delete_award(self, award: Award):
        """Delete an award."""
        await self.request('DELETE', f'/award/{award.id}')

    async def give_award(self, award: Award, account: Account):
        """Give an existing award to a user."""
        await self.request(
            'PUT', f'/account/{account.id}/award/{award.id}',
            response_type=None
        )

    async def take_award(self, award: Award, account: Account):
        """Take an award from a user."""
        await self.request(
            'DELETE', f'/account/{account.id}/award/{award.id}'
        )


class AppClient(AuthenticatedClient):
    """Client that adds endpoints only available to apps."""

    async def create_session(self, account: Account) -> Session:
        """Create a user authentication session."""
        return await self.request(
            'POST', '/auth/create_session', Session,
            json={'account': account.id}
        )

    async def reset_token(self) -> AppCredentials:
        """Reset the authenticated app's token."""
        app = await self.request('POST', '/auth/reset_token', AppCredentials)
        self.auth = aiohttp.BasicAuth(app.username, app.password)
        await self.client.close()
        return app

    async def get_self(self) -> App:
        """Get metadata on the authenticated app."""
        return await self.request('GET', '/auth/me', App)

    async def get_callbacks(self) -> dict[EventType, str]:
        """Get all callbacks registered for this app.

        Returns a dict of event type to callback URL.
        """
        data = (await self.request('GET', '/callbacks'))['callbacks']
        return {EventType(evt): url for evt, url in data.items()}

    async def get_callback(self, event: EventType) -> Callback:
        """Get the callback registered for this app for a given event."""
        return await self.request('GET', f'/callback/{event.value}', Callback)

    async def delete_callback(self, event: EventType):
        """Delete the callback registered for this app for a given event."""
        await self.request('DELETE', f'/callback/{event.value}')

    async def create_callback(
            self, event: EventType, url: str, secret: str) -> Callback:
        """Register a callback for this app for a given event."""
        return await self.request(
            'PUT',
            f'/callback/{event.value}',
            Callback,
            json={'url': url, 'secret': secret}
        )


class UserClient(AuthenticatedClient):
    """Client that adds endpoints only available to users."""

    async def reset_token(self) -> Session:
        """Reset the session token."""
        session = await self.request('POST', '/auth/reset_token', Session)
        self.auth = aiohttp.BasicAuth(session.username, session.password)
        await self.client.close()
        return session

    async def get_self(self) -> Account:
        """Get the account our credentials authenticate us for."""
        return await self.request('GET', '/auth/me', Account)
