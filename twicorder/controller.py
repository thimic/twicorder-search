#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import sys
import time

from threading import Thread

from twicorder import TwicorderException
from twicorder.project_manager import ProjectManager


class WorkerThread(Thread):
    """
    Background thread, running queries.
    """
    def setup(self, func, tasks):
        """
        Preparing thread.

        Args:
            func (func): Function to perform
            tasks (list[twicorder.tasks.Task]): Tasks to perform

        """
        self._running = False
        self._func = func
        self._tasks = tasks

    def stop(self):
        """
        Stop thread.
        """
        self._running = False

    def run(self):
        """
        Start thread.
        """
        from twicorder.exchange import QueryExchange
        self._running = True
        logger.info(' Loading tasks '.center(80, '='))
        logger.info('')
        while self._running:
            update = False
            for task in self._tasks:
                if not task.due:
                    continue
                update = True
                query = self._func(task)
                QueryExchange.add(query)
                logger.info(query)
            if update:
                logger.info('=' * 80)
            # Sleep 1 minute, then wake up and check if any queries are due to
            # run.
            time.sleep(60)


class Twicorder:
    """
    Twicorder controller class.
    """
    def __init__(self, project_dir=None):
        """
        Constructor for Twicorder class. Sets up the task manager, query
        exchange, worker thread and query types.

        Keyword Args:
            project_dir (str): Path to Twicorder project directory

        """
        if project_dir:
            ProjectManager.project_dir = project_dir

        # Todo: Only import logger after project dir is set, to ensure logging
        #       to project dir. This is ugly and needs a better solution.
        from twicorder.utils import TwiLogger
        global logger
        logger = TwiLogger()

        # Test setup before continuing
        try:
            from twicorder.config import Config
            from twicorder.tasks import TaskManager
            from twicorder.auth import Auth
            Config.get()
            TaskManager.load()
            Auth.session()
        except TwicorderException as error:
            logger.critical(error)
            sys.exit(1)
            return

        from twicorder.tasks import TaskManager
        self._task_manager = TaskManager()
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
    def query_types(self):
        """
        Compiles a dictionary of available query types by inspecting the
        twicorder.queries.request_queries module.

        Returns:
            dict: Available query types by name

        """
        if self._query_types:
            return self._query_types
        from twicorder.queries import RequestQuery
        from twicorder.queries import request_queries
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
    twicorder = Twicorder('~/Desktop/Twicorder')
    twicorder.run()
