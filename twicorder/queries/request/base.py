#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import hashlib
import urllib

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Callable, Optional, Set

from twicorder import (
    ForbiddenException,
    RatelimitException,
    UnauthorisedException,
)
from twicorder.appdata import AppData
from twicorder.aio_auth import AsyncAuthHandler
from twicorder.constants import (
    AuthMethod,
    RequestMethod,
)
from twicorder.queries.base import BaseQuery
from twicorder.rate_limits import RateLimitCentral


class BaseRequestQuery(BaseQuery):
    """
    Queries based on the requests module and the twitter API.
    """
    _base_url = 'https://api.twitter.com/1.1'
    _request_method: RequestMethod = RequestMethod.Get
    _auth_methods = {AuthMethod.App, AuthMethod.User}
    _auth_method = AuthMethod.App

    _hash_keys = [
        'endpoint',
        '_results_path',
        '_next_cursor_path',
        '_orig_kwargs',
        '_base_url',
        '_request_method'
    ]

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[BaseRequestQuery], bool]] = None,
                 **kwargs):
        super().__init__(app_data, taskgen, output, max_count, stop_func, **kwargs)

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    @property
    def base_url(self) -> str:
        """
        Base API url for all queries.

        Returns:
            str: API url

        """
        return self._base_url

    @property
    def request_method(self) -> RequestMethod:
        """
        Http request method, such as 'GET' and 'POST'.

        Returns:
            RequestMethod: Request method

        """
        return self._request_method

    @property
    def auth_method(self) -> AuthMethod:
        """
        Twitter API authentication method currently in use. Either App or User
        authentication.

        Returns:
            AuthMethod: App or User auth

        """
        return self._auth_method

    @auth_method.setter
    def auth_method(self, auth_method: AuthMethod):
        """
        Twitter API authentication method currently in use. Either App or User
        authentication.

        Args:
            auth_method (AuthMethod): App or User auth

        """
        self._auth_method = auth_method

    @property
    def auth_methods(self) -> Set[AuthMethod]:
        """
        Available Twitter API authentication methods for this query. Defaults to
        both App and User.

        Returns:
            set[AuthMethod]: Set of authentication methods

        """
        return self._auth_methods

    @property
    def request_url(self) -> str:
        """
        Fully formatted request url constructed from base API url, end point and
        keyword arguments.

        Returns:
            str: Constructed request url

        """
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_method is RequestMethod.Get:
            if self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    @property
    def uid(self) -> str:
        """
        Unique identifier for this query.

        Returns:
            str: Unique identifier

        """
        hash_str = str([getattr(self, k) for k in self._hash_keys]).encode()
        return hashlib.blake2s(hash_str).hexdigest()

    async def setup(self):
        """
        Method called immediately before the query runs.
        """
        await super().setup()
        # Purging logs
        self._log = []

    async def run(self):
        """
        Method that executes main query. Use start() to execute.
        """

        self.log(f'URL: {self.request_url}')
        self.log(f'Method: {self.request_method.name}')
        self.log(f'Auth: {self.auth_method.name}')

        # Perform query
        attempts = 0
        while True:
            try:
                response = await AsyncAuthHandler.request(
                    auth_method=self.auth_method,
                    method=self.request_method,
                    url=self.request_url,
                )
            except Exception as e:
                self.log(f'Request failed: {e}')
                import traceback
                traceback.print_exc()
                attempts += 1
                await asyncio.sleep(2**attempts)
                if attempts >= 5:
                    raise
            else:
                break

        # Check query response code. Return with error message if not a
        # successful 200 code.
        if response.status_code != HTTPStatus.OK:
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                RateLimitCentral.insert(
                    auth_method=self.auth_method,
                    endpoint=self.endpoint,
                    limit=0,
                    remaining=0,
                    reset=(datetime.now() + timedelta(minutes=15)).timestamp()
                )
                msg = '<{r.status_code}> {r.reason_phrase}: {r.text}'.format(r=response)
                raise RatelimitException(msg)
            elif response.status_code == HTTPStatus.UNAUTHORIZED:
                msg = '<{r.status_code}> {r.reason_phrase}: {r.text}'.format(r=response)
                raise UnauthorisedException(msg)
            elif response.status_code == HTTPStatus.FORBIDDEN:
                msg = '<{r.status_code}> {r.reason_phrase}: {r.text}'.format(r=response)
                raise ForbiddenException(msg)
            else:
                self.log(
                    '<{r.status_code}> {r.reason_phrase}: {r.text}'
                    .format(r=response)
                )
            return response
        self.log('Successful return!')

        # Search query response for additional paged results. Pronounce the
        # query done if no more pages are found.
        cursor = response.json().copy()
        if self.next_cursor_path:
            for token in self.next_cursor_path.split('.'):
                cursor = cursor.get(token, {})
            if cursor:
                self._next_cursor = cursor
                self.log('More pages found!')
            else:
                self._next_cursor = None
                self._done = True
                self.log('No more pages!')
        else:
            self._done = True
        self.log(f'Next cursor: {self._next_cursor}')

        # Extract data from query response.
        self._response_data = response.json()
        results = response.json().copy()
        if self.results_path:
            for token in self.results_path.split('.'):
                results = results.get(token, [])
        self._results = results
        if results and isinstance(results, list) and not self._last_cursor:
            first_result = results[0]
            if isinstance(first_result, dict) and 'id' in first_result:
                self._last_cursor = first_result.get('id')
        self._result_count += len(results)
        if self._max_count and self._result_count >= self._max_count:
            self._done = True
        self.log(f'Result count: {len(results)}')

        # Returning crawled results
        return response
