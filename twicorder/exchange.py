#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import create_task, gather, sleep, Queue, Task
from collections import defaultdict
from datetime import timedelta
from typing import Callable, Dict, Optional, Set

from twicorder import (
    ForbiddenException,
    RatelimitException,
    UnauthorisedException,
)
from twicorder.logger import TwiLogger
from twicorder.queries import BaseQuery

logger = TwiLogger()


class QueryQueue(Queue):
    """
    AsyncIO Queue that ignores duplicate items.
    """
    def __init__(self, maxsize=0, *, loop=None):
        super(QueryQueue, self).__init__(maxsize=maxsize, loop=loop)
        self._items = set()

    def _put(self, item) -> None:
        uid = id(item)
        if uid in self._items:
            return
        self._items.add(uid)
        super(QueryQueue, self)._put(item=item)

    def _get(self):
        item = super(QueryQueue, self)._get()
        self._items.remove(id(item))
        return item


async def query_worker(name: str, queue: Queue, on_result: Optional[Callable] = None):
    """
    Fetches query from queue and executes it.
    """
    while True:
        query: BaseQuery = await queue.get()
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
            except UnauthorisedException as error:
                logger.error(error)
                break
                # try_count += 1
                # if try_count <= 3:
                #     await sleep(1)
                #     continue
                # else:
                #     logger.warning(error)
                #     break
            except ForbiddenException as error:
                logger.error(error)
                break
            except RatelimitException as error:
                logger.warning(error)
                await sleep(timedelta(minutes=15).seconds)
                continue
            except Exception:
                # If the query failed, try 5 more times with increasing wait
                # times before giving up.
                try_count += 1
                if try_count <= 5:
                    await sleep(2 ^ try_count)
                    continue
                else:
                    logger.exception(f'Query {query!r} failed:\n')
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
    workers: Dict[str, Set[Task]] = defaultdict(set)
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
            queue = QueryQueue(maxsize=100)
            cls.queues[endpoint] = queue
        return cls.queues[endpoint]

    @classmethod
    def start_workers(cls, endpoint: str, queue: Queue,
                      callback: Optional[Callable] = None,
                      worker_count: int = 4) -> Set[Task]:
        """
        Retrieves the workers for the given endpoint if they exist. If one or
        more worker exists and is alive, return workers. Otherwise create new
        workers and start them.

        Args:
            endpoint: API endpoint
            queue: Work queue for thread
            callback: Callback function that handles query results
            worker_count: Number of workers to create for the given endpoint

        Returns:
            Query workers

        """
        workers = cls.workers.get(endpoint)
        if workers and not all([w.done() for w in workers]):
            return workers
        for i in range(worker_count):
            worker = create_task(
                query_worker(name=endpoint, queue=queue, on_result=callback)
            )
            cls.workers[endpoint].add(worker)
        return cls.workers.get(endpoint)

    @classmethod
    async def add(cls, query, callback=None):
        """
        Finds appropriate queue for given end point and adds it.

        Args:
            query (BaseQuery): Query object
            callback (func): Callback function that handles query results

        """
        queue = cls.get_queue(query.endpoint)
        await queue.put(query)
        cls.start_workers(query.endpoint, queue, callback)

    @classmethod
    def active(cls) -> bool:
        """
        Whether any workers in the QueryExchange are active.

        Returns:
            bool: True if any workers are active, else False

        """
        for endpoint_workers in cls.workers.values():
            for worker in endpoint_workers:
                if not worker.done():
                    return True
        return False

    @classmethod
    def clear(cls):
        """
        Prepares QueryExchange for a new run.
        """
        cls.queues = {}
        cls.workers = {}
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

        # Cancel our workers.
        all_workers = set()
        for endpoint_workers in cls.workers.values():
            for worker in endpoint_workers:
                worker.cancel()
                all_workers.add(worker)
        # Wait until all workers are cancelled.
        await gather(*all_workers, return_exceptions=True)
