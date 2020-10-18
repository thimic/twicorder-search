#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import yaml

from twicorder import NoTasksException
from twicorder.constants import (
    DEFAULT_TASK_FREQUENCY,
    DEFAULT_TASK_ITERATIONS,
    DEFAULT_TASK_KWARGS,
)
from twicorder.tasks.task import Task

from twicorder.tasks.generators.base_generator import BaseTaskGenerator


class ConfigTaskGenerator(BaseTaskGenerator):
    """
    Base task generator. Generates a set of TwiCorder tasks on fetch().
    """

    name = 'config'

    def fetch(self):
        """
        Method to generate tasks. Should populate BaseTaskGenerator._tasks.
        """
        from twicorder.config import Config
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
