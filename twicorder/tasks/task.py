#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time

from typing import Callable, Optional
from weakref import WeakValueDictionary

from twicorder.queries import BaseQuery


class Task:

    stop_func: Optional[Callable[[BaseQuery], bool]] = None

    def __init__(self, name: str, taskgen: str, frequency: int = 15,
                 iterations: int = 0, output: Optional[str] = None, **kwargs):
        self._name = name
        self._taskgen = taskgen
        self._frequency = frequency
        self._iterations = iterations
        self._remaining = iterations
        self._output = output
        self._kwargs = kwargs
        self._queries: WeakValueDictionary[str, BaseQuery] = WeakValueDictionary()

        self._last_run = None

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        string = (
            f'Task('
            f'name={self.name!r}, '
            f'taskgen={self.taskgen!r}, '
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
    def taskgen(self) -> str:
        """
        Name of the generator that created the task.

        Returns:
            Task generator name

        """
        return self._taskgen

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
        if self.done or len(self._queries) > 0:
            return False
        return time.time() - self._last_run >= self.frequency * 60

    @property
    def done(self) -> bool:
        """
        The task is done when there are no more iterations remaining.

        Returns:
            bool: True if all task iterations are done, else False

        """
        alive_queries: WeakValueDictionary[str: BaseQuery] = WeakValueDictionary()
        for uid, query in self._queries.items():
            if query.done:
                self._remaining -= 1
                self._remaining = max(self._remaining, 0)
            else:
                alive_queries[uid] = query
        self._queries = alive_queries

        return self._iterations != 0 and self._remaining == 0

    def add_query(self, query: BaseQuery):
        """
        Add a query to the list of task queries.

        Args:
            query (BaseQuery): Query for this task

        """
        self._last_run = time.time()
        self._queries[id(query)] = query
