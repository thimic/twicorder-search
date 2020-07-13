#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import create_task, gather, sleep, Queue, Task
from typing import Callable, Dict, Optional

from twicorder.logger import TwiLogger

logger = TwiLogger()


class QueryQueue(Queue):
    """
    AsyncIO Queue with queue property exposed.
    """
    @property
    def queue(self):
        return self._queue


async def worker(name: str, queue: Queue, on_result: Optional[Callable] = None):
    """
    Fetches query from queue and executes it.
    """
    while True:
        query = await queue.get()
        if query is None:
            logger.debug(
                f'Terminated worker "{name}" after tombstone query.'
            )
            queue.task_done()
            return
        try_count = 0
        while not query.done:
            try:
                await query.start()
            except Exception:
                logger.exception(f'Query {query!r} failed:\n')
                # If the query failed, try 5 more times with increasing wait
                # times before giving up.
                try_count += 1
                if try_count <= 5:
                    await sleep(2 ^ try_count)
                    continue
                else:
                    break
            if on_result:
                await on_result(query)
            logger.info(query.fetch_log())
            await sleep(0.05)
        queue.task_done()
        if queue.empty():
            break
        await sleep(.1)


class QueryExchange:
    """
    Organises queries in queues and executes them after the FIFO principle.
    """

    queues: Dict[str, QueryQueue] = {}
    tasks: Dict[str, Task] = {}
    failure: bool = False

    @classmethod
    def get_queue(cls, endpoint: str) -> QueryQueue:
        """
        Retrieves the queue for the given endpoint if it exists, otherwise
        creates a queue.

        Args:
            endpoint (str): API endpoint

        Returns:
            Queue: Queue for endpoint

        """
        if not cls.queues.get(endpoint):
            queue = QueryQueue()
            cls.queues[endpoint] = queue
        return cls.queues[endpoint]

    @classmethod
    def start_worker(cls, endpoint: str, queue: Queue, callback=None) -> Task:
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
        task = cls.tasks.get(endpoint)
        if task and not task.done():
            return task
        task = create_task(
            worker(name=endpoint, queue=queue, on_result=callback)
        )
        cls.tasks[endpoint] = task
        return task

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
        queue.put_nowait(query)
        cls.start_worker(query.endpoint, queue, callback)

    @classmethod
    def active(cls) -> bool:
        """
        Whether any threads in the QueryExchange are active.

        Returns:
            bool: True if any threads are active, else False

        """
        return any(not t.done() for t in cls.tasks.values())

    @classmethod
    def clear(cls):
        """
        Prepares QueryExchange for a new run.
        """
        cls.queues = {}
        cls.tasks = {}
        cls.failure = False

    @classmethod
    async def join_wait(cls):
        """
        Sends shutdown signal to threads and waits for all threads and queues to
        terminate.
        """
        # Add tombstone to queues to cancel empty, blocking queues.
        for queue in cls.queues.values():
            await queue.put(None)

        # Cancel our worker tasks.
        for task in cls.tasks.values():
            task.cancel()
        # Wait until all worker tasks are cancelled.
        await gather(*cls.tasks.values(), return_exceptions=True)
