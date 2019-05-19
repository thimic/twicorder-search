#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock

from twicorder.utils import AppData, TwiLogger

logger = TwiLogger()


class RateLimitCentral:
    """
    Class keeping track of end points and their rate limits.
    """
    _limits = {}
    _lock = Lock()

    @classmethod
    def update(cls, endpoint, header):
        """
        Update endpoint with latest rate limit information.

        Args:
            endpoint (str): Endpoint
            header (dict): Query response header

        """
        with cls._lock:
            limit_keys = {
                'x-rate-limit-limit',
                'x-rate-limit-remaining',
                'x-rate-limit-reset'
            }
            if not limit_keys.issubset(header.keys()):
                return
            cls._limits[endpoint] = RateLimit(header)

    @classmethod
    def get(cls, endpoint):
        """
        Retrieves latest rate limit information for the given endpoint.
        Args:
            endpoint (str): Endpoint

        Returns:
            RateLimit: Rate limit object

        """
        with cls._lock:
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


class QueryExchange:
    """
    Organises queries in queues and executes them after the FIFO principle.
    """

    executor = ThreadPoolExecutor(max_workers=None)

    @classmethod
    def on_future_done(cls, future):
        if future.cancelled():
            logger.warning(f'Future {future!r} was cancelled.')
            return
        query = future.result()
        if query.results:
            # Caches found tweet IDs to disk
            query.bake_ids()
            logger.info(f'Cached Tweet IDs to disk!')

        # Caches last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if query.done and query.last_id:
            logger.info(f'Cached ID of last tweet returned by query to disk.')
            AppData.set_last_query_id(query.uid, query.last_id)

        # Re-run the query if there are more pages.
        if not query.done:
            cls.add(query)

    @staticmethod
    def perform_query(query):
        attempts = 0
        while attempts < 9:
            try:
                query.run()
            except Exception:
                logger.exception('Query failed:\n')
                attempts += 1
            else:
                logger.info(query.fetch_log())
                break
            time.sleep(.2 * 2 ** attempts)
        return query

    @classmethod
    def add(cls, query):
        """
        Finds appropriate queue for given end point and adds it.

        Args:
            query (BaseQuery): Query object

        """
        future_result = cls.executor.submit(cls.perform_query, query)
        future_result.add_done_callback(cls.on_future_done)
