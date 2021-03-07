"""Tool to handle pagination."""
from typing import Any, Coroutine

from .types import PaginatedResponse


__all__ = ('Paginator',)


class PaginatorIterator:
    """A class for iterating over paginated results."""

    def __init__(self, get_page: Coroutine):
        """Set up the iterator."""
        self.get_page = get_page
        self.page = 0
        self.buffer = []

    async def __anext__(self) -> list[Any]:
        """Get the next object."""
        if not self.buffer:
            self.buffer = await self.get_page(self.page)
            if not self.buffer:
                raise StopAsyncIteration
            self.page += 1
        return self.buffer.pop(0)


class Paginator:
    """A class capable of retrieving each page of results from a query."""

    def __init__(
            self, method: str, path: str, client: Any,
            params: dict[str, Any] = None, data_type: Any = None):
        """Store the setup for the paginator."""
        self.method = method
        self.path = path
        self.client = client
        self.params = params or {}
        self.data_type = data_type
        self.iter_page = 0
        self.meta: PaginatedResponse = None

    async def get_page(self, page_number: int) -> list[Any]:
        """Get a page of results (0-indexed)."""
        self.params['page'] = page_number
        data = await self.client.request(
            self.method, self.path, params=self.params,
            response_type=PaginatedResponse
        )
        if self.data_type:
            values = data.parse_as(self.data_type)
        else:
            values = data.data
        self.meta = data
        return values

    def __aiter__(self) -> PaginatorIterator:
        """Iterate over the results."""
        return PaginatorIterator(self.get_page)
