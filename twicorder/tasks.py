#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import yaml

from twicorder import NoTasksException
from twicorder.project_manager import ProjectManager
from twicorder.utils import TwiLogger

logger = TwiLogger()


class Task:

    def __init__(self, name, frequency=15, output=None, **kwargs):
        self._name = name
        self._frequency = frequency
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
            f'multipart={self.multipart}, '
            f'kwargs={str(self.kwargs)}'
            f')'
        )
        return string

    @property
    def name(self):
        return self._name

    @property
    def frequency(self):
        return self._frequency

    @property
    def output(self):
        return self._output

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def due(self):
        if self._last_run is None:
            self._last_run = time.time()
            return True
        if time.time() - self._last_run >= self.frequency * 60:
            self._last_run = time.time()
            return True
        return False


class TaskManager:

    _tasks = []

    @classmethod
    def load(cls):
        """
        Reading tasks from yaml file and parsing to a dictionary.
        """
        cls._tasks = []
        if not os.path.isfile(ProjectManager.tasks):
            raise NoTasksException
        with open(ProjectManager.tasks, 'r') as stream:
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
