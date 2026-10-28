"""Tests for MyLight Systems API."""

import json
from urllib.parse import parse_qsl, urlsplit

from aresponses import Response
from aresponses.main import Route


class _GetRoute(Route):
    """Match host, path and query string regardless of parameter order."""

    def __init__(self, url):
        parts = urlsplit(url)
        super().__init__(method_pattern="get", host_pattern=parts.netloc, path_pattern=parts.path)
        self._query = sorted(parse_qsl(parts.query, keep_blank_values=True))

    async def matches(self, request):
        query = sorted(parse_qsl(request.query_string, keep_blank_values=True))
        return query == self._query and await super().matches(request)


def mock_get(aresponses, url, payload, status=200):
    """Register a one-shot GET route answering `payload` as JSON."""
    response = Response(status=status, content_type="application/json", text=json.dumps(payload))
    aresponses.add(route=_GetRoute(url), response=response)
