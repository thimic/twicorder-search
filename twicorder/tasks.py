#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import time
import yaml

from typing import List

from twicorder import NoTasksException
from twicorder.constants import (
    DEFAULT_TASK_FREQUENCY,
    DEFAULT_TASK_ITERATIONS,
    DEFAULT_TASK_KWARGS,
)


class Task:

    def __init__(self, name, frequency=15, iterations=0, output=None, **kwargs):
        self._name = name
        self._frequency = frequency
        self._iterations = iterations
        self._remaining = iterations
        self._output = output
        self._kwargs = kwargs
        self._queries = []

        self._last_run = None

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        string = (
            f'Task('
            f'name={self.name!r}, '
            f'frequency={self.frequency}, '
            f'iterations={self.iterations}, '
            f'output={self.output!r}, '
            f'kwargs={str(self.kwargs)}'
            f')'
        )
        return string

    @property
    def name(self) -> str:
        """
        Task name.

        Returns:
            str: Task name

        """
        return self._name

    @property
    def frequency(self) -> int:
        """
        Frequency with which to repeat the task in minutes.

        Returns:
            int: Task repeat frequency

        """
        return self._frequency

    @property
    def iterations(self) -> int:
        """
        Number of times to iterate over the task. A value of 0 will iterate
        indefinitely.

        Returns:
            int: Number of iterations

        """
        return self._iterations

    @property
    def remaining(self) -> int:
        """
        Number of iterations remaining for this task.

        Returns:
            int: Number of remaining iterations

        """
        return self._remaining

    @property
    def output(self) -> str:
        """
        Task result output path, relative to output directory.

        Returns:
            str: Task result output relative path

        """
        return self._output

    @property
    def kwargs(self) -> dict:
        """
        Additional keyword arguments for the task.

        Returns:
            dict: Additional keyword arguments

        """
        return self._kwargs

    @property
    def due(self) -> bool:
        """
        Checks if task is due to be run, based on given number of iterations and
        frequency.

        Returns:
            bool: True if task is due to run, else False

        """
        if self._last_run is None:
            return True
        return time.time() - self._last_run >= self.frequency * 60

    @property
    def done(self) -> bool:
        """
        The task is done when there are no more iterations remaining.

        Returns:
            bool: True if all task iterations are done, else False

        """
        alive_queries = []
        for query in self._queries:
            if query.done:
                self._remaining -= 1
            else:
                alive_queries.append(query)
        self._queries = alive_queries

        return self._iterations != 0 and self._remaining == 0

    def add_query(self, query: 'BaseQuery'):
        """
        Add a query to the list of task queries.

        Args:
            query (BaseQuery): Query for this task

        """
        self._last_run = time.time()
        self._queries.append(query)


class TaskManager:

    def __init__(self):
        """
        Reading tasks from yaml file and parsing to a dictionary.
        """
        from twicorder.config import Config
        self._tasks = []
        if not os.path.isfile(Config.task_file):
            raise NoTasksException
        with open(Config.task_file, 'r') as stream:
            raw_tasks = yaml.full_load(stream)
        for query, tasks in raw_tasks.items():
            for raw_task in tasks or []:
                frequency = raw_task.get('frequency') or DEFAULT_TASK_FREQUENCY
                iters = raw_task.get('iterations') or DEFAULT_TASK_ITERATIONS
                task = Task(
                    name=query,
                    frequency=frequency,
                    iterations=iters,
                    output=raw_task.get('output') or query,
                    max_count=raw_task.get('max_count') or 0,
                    **raw_task.get('kwargs') or DEFAULT_TASK_KWARGS
                )
                self._tasks.append(task)

    @property
    def tasks(self) -> List[Task]:
        """
        List of available tasks that are not finished.

        Returns:
            list[Task]: List of remaining tasks

        """
        self._tasks = [t for t in self._tasks if not t.done]
        return self._tasks
