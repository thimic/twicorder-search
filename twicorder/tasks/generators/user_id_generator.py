#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Set

from twicorder import NoTasksException
from twicorder.tasks.task import Task

from twicorder.tasks.generators.base_generator import BaseTaskGenerator


class UserIDTaskGenerator(BaseTaskGenerator):
    """
    User ID based task generator. Generates a set of TwiCorder tasks on fetch(),
    based on the given name pattern. The name pattern is a glob pattern used to
    find files containing delimited Twitter user IDs in plain text format.
    """

    name = 'user_id'

    def __init__(self, name_pattern: str, delimiter: str = '\n'):
        """
        Entry point for UserIDTaskGenerator.

        Args:
            name_pattern: Glob name pattern
            delimiter: Tweet ID delimiter. Dafaults to new line.

        """
        super(UserIDTaskGenerator, self).__init__()
        self._name_pattern = name_pattern
        self._delimiter = delimiter

    def fetch(self):
        """
        Method to generate tasks. Should populate UserIDTaskGenerator._tasks.
        """

        user_ids: Set[str] = set()

        for filepath in Path('/').glob(self._name_pattern.lstrip('/')):
            user_ids.update(filepath.read_text().splitlines())

        sorted_user_ids = sorted(user_ids, key=lambda x: int(x))

        if not user_ids:
            msg = (
                f'Found no files containing user IDs for name pattern '
                f'{self._name_pattern!r}.'
            )
            raise NoTasksException(msg)

        ids_per_request = 100
        request_chunks = [
            sorted_user_ids[i:i + ids_per_request]
            for i in range(0, len(sorted_user_ids), ids_per_request)
        ]
        for request_chunk in request_chunks:
            self._tasks.append(
                Task(
                    name='user_lookups',
                    frequency=10000,
                    iterations=1,
                    output='user_lookups',
                    user_id=','.join(request_chunk)
                )
            )
