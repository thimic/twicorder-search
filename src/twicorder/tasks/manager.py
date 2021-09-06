#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Tuple

from twicorder.appdata import AppData
from twicorder.tasks.generators import load_generators
from twicorder.tasks.task import Task


class TaskManager:

    def __init__(self, app_data: AppData, generators: List[Tuple[str, dict]]):
        """
        Reading tasks from yaml file and parsing to a dictionary.

        Args:
            app_data: AppData object for persistent storage between sessions
            generators: Generator names and kwargs

        """
        self._app_data = app_data
        self._generators = generators or [('config', {})]
        self._tasks: List[Task] = []

    async def load(self):
        """
        Asynchronously load tasks from all task generators.
        """
        all_generators = load_generators()

        for generator_name, kwargs in self._generators:
            task_generator = all_generators[generator_name](
                app_data=self._app_data,
                **kwargs
            )
            await task_generator.fetch()
            self._tasks += task_generator.tasks

    @property
    def tasks(self) -> List[Task]:
        """
        List of available tasks that are not finished.

        Returns:
            list[Task]: List of remaining tasks

        """
        self._tasks = [t for t in self._tasks if not t.done]
        return self._tasks
