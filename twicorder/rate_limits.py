#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime


class RateLimitCentral:
    """
    Class keeping track of end points and their rate limits.
    """
    _limits = {}

    @classmethod
    def update(cls, endpoint, header):
        """
        Update endpoint with latest rate limit information.

        Args:
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
        cls._limits[endpoint] = RateLimit(header)

    @classmethod
    def insert(cls, endpoint: str, cap: int, remaining: int, reset: float):
        """
        Create rate limit object from values, rather than headers.

        Args:
            endpoint (str): Endpoint
            cap (int): Query cap for the given endpoint
            remaining (int): Remaining queries for the given endpoint
            reset (float): Time until the current 15 minute window expires

        """
        cls._limits[endpoint] = RateLimit.create(cap, remaining, reset)

    @classmethod
    def get(cls, endpoint):
        """
        Retrieves latest rate limit information for the given endpoint.
        Args:
            endpoint (str): Endpoint

        Returns:
            RateLimit: Rate limit object

        """
        return cls._limits.get(endpoint)

    @classmethod
    def get_cap(cls, endpoint):
        """
        Retrieve the query cap for the given endpoint.

        Args:
            endpoint (str): Endpoint

        Returns:
            int: Max queries per 15 minutes

        """
        limit = cls.get(endpoint)
        if not limit:
            return
        return limit.cap

    @classmethod
    def get_remaining(cls, endpoint):
        """
        Retrieve number of remaining queries for the given endpoint.

        Args:
            endpoint (str): Endpoint

        Returns:
            int: Remaining queries for the current 15 minute window

        """
        limit = cls.get(endpoint)
        if not limit:
            return
        return limit.remaining

    @classmethod
    def get_reset(cls, endpoint):
        """
        Retrieve time until the current 15 minute window expires.

        Args:
            endpoint (str): Endpoint

        Returns:
            float: Time in seconds

        """
        limit = cls.get(endpoint)
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
            cap (int): Query cap for the given endpoint
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
            f'RateLimit(cap={self.cap}, remaining={self.remaining}, '
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
