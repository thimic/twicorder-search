#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from queue import Queue
from threading import Thread

from twicorder.utils import TwiLogger

logger = TwiLogger()


class QueryWorker(Thread):
    """
    Queue thread, used to execute queue queries.
    """

    def __init__(self, *args, **kwargs):
        super(QueryWorker, self).__init__(*args, **kwargs)
        self._query = None

    def setup(self, queue, on_result=None):
        self._queue = queue
        self._on_result = on_result

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
                if self._on_result:
                    self._on_result(self.query)
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
            thread.setup(queue=queue, on_result=cls.on_result)
            thread.start()
            cls.threads[endpoint] = thread
        return cls.queues[endpoint]

    @staticmethod
    def on_result(query):
        # Todo: Perform query action, such as save!
        print(f'Received result from {query}')

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
