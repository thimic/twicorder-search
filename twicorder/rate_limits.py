#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

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
    def update(cls, auth_method: AuthMethod, endpoint: str, header: dict):
        """
        Update endpoint with latest rate limit information.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint
            header (dict): Query response header

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
    def _load_rate_limits(cls, auth_method: AuthMethod):
        """
        Load all rate limits.

        Args:
            auth_method (AuthMethod): Authentication method

        """
        from twicorder.queries.request_queries import RateLimitStatusQuery
        query = RateLimitStatusQuery()
        query.auth_method = auth_method
        results = query.start()
        for resource, family in results['resources'].items():
            for endpoint, limit_data in family.items():
                cls.insert(
                    auth_method=auth_method,
                    endpoint=endpoint,
                    **limit_data
                )

    @classmethod
    def get(cls, auth_method: AuthMethod, endpoint: str):
        """
        Retrieves latest rate limit information for the given endpoint.
        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint

        Returns:
            RateLimit: Rate limit object

        """
        if not cls._limits[auth_method].get(endpoint):
            cls._load_rate_limits(auth_method)
        return cls._limits[auth_method].get(endpoint)

    @classmethod
    def get_cap(cls, auth_method: AuthMethod, endpoint: str):
        """
        Retrieve the query limit for the given endpoint.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint

        Returns:
            int: Max queries per 15 minutes

        """
        limit = cls.get(auth_method, endpoint)
        if not limit:
            return
        return limit.cap

    @classmethod
    def get_remaining(cls, auth_method: AuthMethod, endpoint: str):
        """
        Retrieve number of remaining queries for the given endpoint.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint

        Returns:
            int: Remaining queries for the current 15 minute window

        """
        limit = cls.get(auth_method, endpoint)
        if not limit:
            return
        return limit.remaining

    @classmethod
    def get_reset(cls, auth_method: AuthMethod, endpoint: str):
        """
        Retrieve time until the current 15 minute window expires.

        Args:
            auth_method (AuthMethod): Authentication method
            endpoint (str): Endpoint

        Returns:
            float: Time in seconds

        """
        limit = cls.get(auth_method, endpoint)
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
        reset = datetime.fromtimestamp(self._reset)
        representation = (
            f'RateLimit(limit={self.cap}, remaining={self.remaining}, '
            f'reset="{reset:%y.%m.%d %H:%M:%S}")'
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
