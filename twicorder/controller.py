#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os
import sys
import time

from twicorder import TwicorderException
from twicorder.config import Config
from twicorder.utils import TwiLogger

logger = TwiLogger()


class Twicorder:
    """
    Twicorder controller class.
    """
    def __init__(self, clear_cache=False, purge_logs=False):
        """
        Constructor for Twicorder class. Sets up the task manager, query
        exchange, worker thread and query types.

        Keyword Args:
            clear_cache (bool): Clear application cache and exit
            purge_logs (bool): Purge logs and exit

        """

        # Check application mode
        if clear_cache:
            os.remove(Config.appdata)
            logger.info(f'Cleared cache: {Config.appdata}')
        if purge_logs:
            os.remove(Config.logs)
            logger.info(f'Purged logs: {Config.logs}')
        if clear_cache or purge_logs:
            sys.exit(0)

        # Test setup before continuing
        try:
            from twicorder.tasks import TaskManager
            from twicorder.auth import Auth
            TaskManager.load()
            Auth.session()
        except TwicorderException as error:
            logger.critical(error)
            sys.exit(1)

        from twicorder.tasks import TaskManager

        self._task_manager = TaskManager()
        self._query_types = {}
        self._running = False

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
        self._running = False

    def run(self):
        """
        Starts crawler.
        """
        self._running = True
        from twicorder.exchange import QueryExchange
        logger.info(' Loading tasks '.center(80, '='))
        logger.info('')
        slept = 0
        try:
            while self._running:
                # Sleep 1 minute, then wake up and check if any queries are due to
                # run. Don't sleep on first run.
                if not 0 < slept <= 60:
                    slept = 1
                    update = False

                    # Remove completed one time tasks from previous run
                    tasks_done = []
                    for task in tasks_done:
                        self.tasks.remove(task)

                    for task in self.tasks:
                        if not task.due:
                            if not task.repeating:
                                # Flag completed one time tasks as done
                                tasks_done.append(task)
                            continue
                        update = True
                        query = self.cast_query(task)
                        # Todo: Finish callback logic!
                        QueryExchange.add(query, callback)
                        logger.info(query)
                    if update:
                        logger.info('=' * 80)
                    continue
                # Sleep 1 second, count the number of seconds slept and continue.
                time.sleep(1)
                slept += 1
        except KeyboardInterrupt:
            logger.info('\n' + '=' * 80)
            logger.info('Exiting...')
            logger.info('=' * 80 + '\n')
        QueryExchange.join_wait()

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
