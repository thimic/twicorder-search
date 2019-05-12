#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from datetime import datetime
from queue import Queue
from threading import Thread

from twicorder.utils import TwiLogger

logger = TwiLogger()


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


class QueryWorker(Thread):
    """
    Queue thread, used to execute queue queries.
    """

    def __init__(self, *args, **kwargs):
        super(QueryWorker, self).__init__(*args, **kwargs)
        self._query = None

    def setup(self, queue):
        self._queue = queue

    @property
    def queue(self):
        return self._queue

    @property
    def query(self):
        return self._query

    def run(self):
        """
        Fetches query from queue and executes it.
        """
        while True:
            self._query = self.queue.get()
            if self.query is None:
                logger.info(f'Terminating thread "{self.name}"')
                break
            while not self.query.done:
                try:
                    self.query.run()
                except Exception:
                    logger.exception('Query failed:\n')
                    break
                logger.info(self.query.fetch_log())
                time.sleep(.2)
            time.sleep(.5)
            self.queue.task_done()


class QueryExchange:
    """
    Organises queries in queues and executes them after the FIFO principle.
    """

    queues = {}
    threads = {}
    failure = False

    @classmethod
    def get_queue(cls, endpoint):
        """
        Retrieves the queue for the given endpoint if it exists, otherwise
        creates a queue.

        Args:
            endpoint (str): API endpoint

        Returns:
            Queue: Queue for endpoint

        """
        if not cls.queues.get(endpoint):
            queue = Queue()
            cls.queues[endpoint] = queue
            thread = QueryWorker(name=endpoint)
            thread.setup(queue=queue)
            thread.start()
            cls.threads[endpoint] = thread
        return cls.queues[endpoint]

    @classmethod
    def add(cls, query):
        """
        Finds appropriate queue for given end point and adds it.

        Args:
            query (BaseQuery): Query object

        """
        queue = cls.get_queue(query.endpoint)
        if query in queue.queue:
            logger.info(f'Query with ID {query.uid} is already in the queue.')
            return
        thread = cls.threads.get(query.endpoint)
        if thread and thread.query == query:
            logger.info(f'Query with ID {query.uid} is already running.')
            return
        queue.put(query)

    @classmethod
    def clear(cls):
        """
        Prepares QueryExchange for a new run.
        """
        cls.queues = {}
        cls.threads = {}
        cls.failure = False

    @classmethod
    def wait(cls):
        """
        Sends shutdown signal to threads and waits for all threads and queues to
        terminate.
        """
        for queue in cls.queues.values():
            queue.put_nowait(None)
        for thread in cls.threads.values():
            thread.join()
