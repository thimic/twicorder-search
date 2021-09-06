#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from datetime import datetime, timezone

from httpx import Headers
from twicorder.appdata import AppData
from twicorder.constants import AuthMethod


class RateLimitCentral:
    """
    Class keeping track of end points and their rate limits.
    """
    _limits = {
        AuthMethod.App: {},
        AuthMethod.User: {}
    }

    @classmethod
    def update(cls, auth_method: AuthMethod, endpoint: str, header: Headers):
        """
        Update endpoint with latest rate limit information.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint: Endpoint
            header: Query response header

        """
        limit_keys = {
            'x-rate-limit-limit',
            'x-rate-limit-remaining',
            'x-rate-limit-reset'
        }
        if not limit_keys.issubset(header.keys()):
            return
        cls._limits[auth_method][endpoint] = RateLimit(header)

    @classmethod
    def insert(cls, auth_method: AuthMethod, endpoint: str, limit: int,
               remaining: int, reset: float):
        """
        Create rate limit object from values, rather than headers.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint
            limit (int): Query cap for the given endpoint
            remaining (int): Remaining queries for the given endpoint
            reset (float): Time until the current 15 minute window expires

        """
        cls._limits[auth_method][endpoint] = RateLimit.create(
            limit,
            remaining,
            reset
        )

    @classmethod
    async def _load_rate_limits(cls, app_data: AppData, auth_method: AuthMethod):
        """
        Load all rate limits.

        Args:
            app_data: AppData object for persistent storage between sessions
            auth_method (AuthMethod): Authentication method

        """
        from twicorder.queries.request.endpoints import RateLimitStatusQuery
        query = RateLimitStatusQuery(app_data, 'twicorder')
        query.auth_method = auth_method
        results = await query.start()
        for resource, family in results['resources'].items():
            for endpoint, limit_data in family.items():
                cls.insert(
                    auth_method=auth_method,
                    endpoint=endpoint,
                    **limit_data
                )

    @classmethod
    async def get(cls, app_data: AppData, auth_method: AuthMethod,
                  endpoint: str) -> RateLimit:
        """
        Retrieves latest rate limit information for the given endpoint.

        Args:
            app_data: AppData object for persistent storage between sessions
            auth_method: Authentication method
            endpoint: Endpoint

        Returns:
            Rate limit object

        """
        if not cls._limits[auth_method].get(endpoint):
            await cls._load_rate_limits(app_data, auth_method)
        return cls._limits[auth_method].get(endpoint)

    @classmethod
    async def get_cap(cls, app_data: AppData, auth_method: AuthMethod,
                      endpoint: str) -> Optional[int]:
        """
        Retrieve the query limit for the given endpoint.

        Args:
            app_data:
            auth_method: Authentication method
            endpoint: Endpoint

        Returns:
            Max queries per 15 minutes

        """
        limit = await cls.get(app_data, auth_method, endpoint)
        if not limit:
            return
        return limit.cap

    @classmethod
    async def get_remaining(cls, app_data: AppData, auth_method: AuthMethod,
                            endpoint: str) -> Optional[int]:
        """
        Retrieve number of remaining queries for the given endpoint.

        Args:
            app_data: AppData object for persistent storage between sessions
            auth_method: Authentication method
            endpoint: Endpoint

        Returns:
            Remaining queries for the current 15 minute window

        """
        limit = await cls.get(app_data, auth_method, endpoint)
        if not limit:
            return
        return limit.remaining

    @classmethod
    async def get_reset(cls, app_data: AppData, auth_method: AuthMethod,
                        endpoint: str) -> Optional[float]:
        """
        Retrieve time until the current 15 minute window expires.

        Args:
            app_data: AppData object for persistent storage between sessions
            auth_method: Authentication method
            endpoint: Endpoint

        Returns:
            Time in seconds to reset

        """
        limit = await cls.get(app_data, auth_method, endpoint)
        if not limit:
            return
        return limit.reset


class RateLimit:
    """
    Rate limit object, used to describe the limits for a given API end point.
    """
    def __init__(self, headers):
        self._cap = headers.get('x-rate-limit-limit')
        self._remaining = int(headers.get('x-rate-limit-remaining'))
        self._reset = float(headers.get('x-rate-limit-reset'))

    @classmethod
    def create(cls, cap: int, remaining: int, reset: float) -> RateLimit:
        """
        Create rate limit object from values, rather than headers.

        Args:
            cap (int): Query limit for the given endpoint
            remaining (int): Remaining queries for the given endpoint
            reset (float): Time until the current 15 minute window expires

        Returns:
            RateLimit: Rate limit object

        """
        headers = {
            'x-rate-limit-limit': cap,
            'x-rate-limit-remaining': remaining,
            'x-rate-limit-reset': reset
        }
        return RateLimit(headers)

    def __repr__(self):
        reset = datetime.fromtimestamp(self._reset, timezone.utc)
        local_reset = reset.astimezone()
        representation = (
            f'RateLimit(limit={self.cap}, remaining={self.remaining}, '
            f'reset="{local_reset:%y.%m.%d %H:%M:%S}")'
        )
        return representation

    @property
    def cap(self):
        """
        Queries allowed per 15 minutes.

        Returns:
            int: Number of queries

        """
        return self._cap

    @property
    def remaining(self):
        """
        Queries left for the current 15 minute window.

        Returns:
            int: Number of queries

        """
        return self._remaining

    @property
    def reset(self):
        """
        Time until the current 15 minute window expires.

        Returns:
            float: Reset time

        """
        return self._reset
