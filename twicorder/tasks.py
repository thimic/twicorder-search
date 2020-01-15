#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import yaml

from twicorder import NoTasksException
from twicorder.config import Config
from twicorder.utils import TwiLogger

logger = TwiLogger()


class Task:

    def __init__(self, name, frequency=15, iterations=0, output=None, **kwargs):
        self._name = name
        self._frequency = frequency
        self._iterations = iterations
        self._remaining = iterations
        self._output = output
        self._kwargs = kwargs

        self._last_run = None

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        string = (
            f'Task('
            f'name={repr(self.name)}, '
            f'frequency={repr(self.frequency)}, '
            f'iterations={repr(self.iterations)}, '
            f'multipart={self.multipart}, '
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
            self._last_run = time.time()
            return True
        if time.time() - self._last_run >= self.frequency * 60:
            self._last_run = time.time()
            return True
        return False

    @property
    def done(self) -> bool:
        """
        The task is done when there are no more iterations remaining.

        Returns:
            bool: True if all task iterations are done, else False

        """
        return self._iterations != 0 and self._remaining == 0

    def checkout(self):
        """
        Decrements remaining iterations with one for tasks with a finite number
        of iterations.
        """
        if self._iterations > 0 and self._remaining > 0:
            self._remaining -= 1



class TaskManager:

    _tasks = []

    @classmethod
    def load(cls):
        """
        Reading tasks from yaml file and parsing to a dictionary.
        """
        cls._tasks = []
        if not os.path.isfile(Config.task_file):
            raise NoTasksException
        with open(Config.task_file, 'r') as stream:
            raw_tasks = yaml.full_load(stream)
        for query, tasks in raw_tasks.items():
            for raw_task in tasks or []:
                task = Task(
                    name=query,
                    frequency=raw_task.get('frequency') or 15,
                    output=raw_task.get('output'),
                    **raw_task.get('kwargs') or {}
                )
                cls._tasks.append(task)

    @property
    def tasks(self):
        if not self._tasks:
            self.load()
        return self._tasks
