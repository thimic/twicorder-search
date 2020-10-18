#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Tuple

from twicorder.tasks.generators import load_generators
from twicorder.tasks.task import Task


class TaskManager:

    def __init__(self, generators: List[Tuple[str, dict]]):
        """
        Reading tasks from yaml file and parsing to a dictionary.

        Args:
            generators: Generator names and kwargs

        """
        all_generators = load_generators()

        self._tasks: List[Task] = []

        for generator_name, kwargs in generators:
            task_generator = all_generators[generator_name](**kwargs)
            task_generator.fetch()
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


if __name__ == '__main__':
    generators = [
        ('user_id', {'name_pattern': '/Users/thimic/Desktop/follower_ids/*.txt'})
    ]
    manager = TaskManager(generators)
    print(len(manager.tasks))
    from pprint import pprint
    pprint(manager.tasks[0]._kwargs)
    pprint(len(manager.tasks[0]._kwargs['user_id'].split(',')))
    pprint(len(manager.tasks[-1]._kwargs['user_id'].split(',')))

