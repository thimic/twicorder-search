#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from queue import Queue
from threading import Thread

from twicorder.logging import TwiLogger

logger = TwiLogger()


class QueryWorker(Thread):
    """
    Queue thread, used to execute queue queries.
    """

    def __init__(self, *args, **kwargs):
        super(QueryWorker, self).__init__(*args, **kwargs)
        self._query = None
        self._running = True

    def setup(self, queue, on_result=None):
        self._queue = queue
        self._on_result = on_result

    def cancel(self):
        self._running = False
        self.join()
        logger.debug(f'Terminated thread "{self.name}" after call to cancel.')

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
        self._running = True
        while self._running:
            # Blocking call
            self._query = self.queue.get()
            if self.query is None:
                logger.debug(
                    f'Terminated thread "{self.name}" after tombstone query.'
                )
                break
            while not self.query.done and self._running:
                try:
                    self.query.start()
                except Exception:
                    logger.exception('Query failed:\n')
                    break
                if self._on_result:
                    self._on_result(self.query)
                logger.info(self.query.fetch_log())
                time.sleep(.2)
            self._query = None
            self.queue.task_done()
            if self.queue.empty():
                break
            time.sleep(.5)


class QueryExchange:
    """
    Organises queries in queues and executes them after the FIFO principle.
    """

    queues = {}
    threads = {}
    failure = False

    @classmethod
    def get_queue(cls, endpoint: str) -> Queue:
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
        return cls.queues[endpoint]

    @classmethod
    def start_thread(cls, endpoint: str, queue: Queue, callback=None) -> QueryWorker:
        """
        Retrieves the thread for the given endpoint if it exists. If a thread
        exists and is alive, return it. Otherwise create a new thread and start
        it.

        Args:
            endpoint (str): API endpoint
            queue (Queue): Work queue for thread
            callback (func): Callback function that handles query results

        Returns:
            QueryWorker: Worker thread

        """
        thread = cls.threads.get(endpoint)
        if thread and thread.is_alive():
            return thread
        thread = QueryWorker(name=endpoint)
        thread.setup(queue=queue, on_result=callback)
        thread.start()
        cls.threads[endpoint] = thread
        return thread

    @classmethod
    def add(cls, query, callback=None):
        """
        Finds appropriate queue for given end point and adds it.

        Args:
            query (BaseQuery): Query object
            callback (func): Callback function that handles query results

        """
        queue = cls.get_queue(query.endpoint)
        if query in queue.queue:
            logger.info(f'Query with ID {query.uid} is already in the queue.')
            return
        cls.start_thread(query.endpoint, queue, callback)
        queue.put(query)

    @classmethod
    def active(cls) -> bool:
        """
        Whether any threads in the QueryExchange are active.

        Returns:
            bool: True if any threads are active, else False

        """
        return any(t.is_alive() for t in cls.threads.values())

    @classmethod
    def clear(cls):
        """
        Prepares QueryExchange for a new run.
        """
        cls.queues = {}
        cls.threads = {}
        cls.failure = False

    @classmethod
    def join_wait(cls):
        """
        Sends shutdown signal to threads and waits for all threads and queues to
        terminate.
        """
        # Add tombstone to queues to cancel empty, blocking queues.
        for queue in cls.queues.values():
            queue.put(None)

        # Stop threads in progress
        for thread in cls.threads.values():
            thread.cancel()
