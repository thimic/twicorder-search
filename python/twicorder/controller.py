#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import time

from threading import Thread

from twicorder.exchange import QueryExchange
from twicorder.tasks import TaskManager
from twicorder.queries import RequestQuery
from twicorder.queries import request_queries


class WorkerThread(Thread):
    """
    Background thread, running queries.
    """
    def setup(self, func, tasks, query_exchange):
        """
        Preparing thread.

        Args:
            func (func): Function to perform
            tasks (list[twicorder.tasks.Task]): Tasks to perform
            query_exchange (twicorder.exchange.QueryExchange): Query exchange
                instance

        """
        self._running = False
        self._func = func
        self._tasks = tasks
        self._query_exchange = query_exchange

    def stop(self):
        """
        Stop thread.
        """
        self._running = False

    def run(self):
        """
        Start thread.
        """
        self._running = True
        while self._running:
            for task in self._tasks:
                if not task.due:
                    continue
                self._query_exchange.add(self._func(task))
            # Sleep 1 minute, then wake up and check if any queries are due to
            # run.
            time.sleep(60)


class Twicorder:
    """
    Twicorder controller class.
    """
    def __init__(self):
        """
        Constructor for Twicorder class. Sets up the task manager, query
        exchange, worker thread and query types.
        """
        self._task_manager = TaskManager()
        self._query_exchange = QueryExchange()
        self._worker_thread = WorkerThread()
        self._query_types = {}

    @property
    def task_manager(self):
        """
        Task manager instance for Twicorder.

        Returns:
            twicorder.tasks.TaskManager: Task manager instance

        """
        return self._task_manager

    @property
    def tasks(self):
        """
        List of tasks registered in the task manager.

        Returns:
            list[twicorder.tasks.Task]: List of tasks

        """
        return self._task_manager.tasks

    @property
    def query_exchange(self):
        """
        Query exchange instance for Twicorder.

        Returns:
            twicorder.exchange.QueryExchange: Query Exchange

        """
        return self._query_exchange

    @property
    def query_types(self):
        """
        Compiles a dictionary of available query types by inspecting the
        twicorder.queries.request_queries module.

        Returns:
            dict: Available query types by name

        """
        if self._query_types:
            return self._query_types
        for name, item in inspect.getmembers(request_queries, inspect.isclass):
            if item == RequestQuery:
                continue
            elif issubclass(item, RequestQuery):
                self._query_types[item.name] = item
        return self._query_types

    def stop(self):
        """
        Stops crawler.
        """
        self._worker_thread.stop()

    def run(self):
        """
        Starts crawler.
        """
        self._worker_thread.setup(
            func=self.cast_query,
            tasks=self.tasks,
            query_exchange=self.query_exchange
        )
        self._worker_thread.start()

    def cast_query(self, task):
        """
        Casts the given task to a query.

        Args:
            task (twicorder.tasks.Task): Task

        Returns:
            twicorder.queries.BaseQuery: Query


        """
        query_object = self.query_types[task.name]
        query = query_object(task.output, **task.kwargs)
        return query


if __name__ == '__main__':
    twicorder = Twicorder()
    twicorder.run()
