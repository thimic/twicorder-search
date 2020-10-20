#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Set

from twicorder import NoTasksException
from twicorder.tasks.task import Task

from twicorder.tasks.generators.base_generator import BaseTaskGenerator


class UserLookupTaskGenerator(BaseTaskGenerator):
    """
    User lookup task generator. Generates a set of TwiCorder tasks to look up
    user objects on fetch(), based on files matching the given name pattern. The
    files specified by the pattern should contain delimited Twitter user IDs or
    screen names in plain text format.
    """

    class LookupMethod(Enum):
        Id = 'id'
        Username = 'username'

    name = 'user_lookups'

    def __init__(self, name_pattern: str, delimiter: str = '\n',
                 lookup_method: str = 'id'):
        """
        Entry point for UserLookupTaskGenerator.

        Args:
            name_pattern: Glob name pattern
            delimiter: User ID/name delimiter. Defaults to new line.
            lookup_method: "id" if looking up user ids or "username" if looking
                           up user names

        """
        super().__init__()
        self._name_pattern = name_pattern
        self._delimiter = delimiter
        self._lookup_method = self.LookupMethod(lookup_method)

    def fetch(self):
        """
        Method to generate tasks. Should populate UserLookupTaskGenerator._tasks.
        """
        users: Set[str] = set()

        for filepath in Path('/').glob(self._name_pattern.lstrip('/')):
            users.update(filepath.read_text().splitlines())

        if self._lookup_method == self.LookupMethod.Id:
            sorted_users = sorted(users, key=lambda x: int(x))
        else:
            sorted_users = sorted(users)

        if not sorted_users:
            msg = (
                f'Found no files containing usernames or IDs for name pattern '
                f'{self._name_pattern!r}.'
            )
            raise NoTasksException(msg)

        users_per_query = 100
        request_chunks = [
            sorted_users[i:i + users_per_query]
            for i in range(0, len(sorted_users), users_per_query)
        ]
        for request_chunk in request_chunks:
            kwargs = dict(
                name='user_lookups',
                frequency=10000,
                iterations=1,
                output='user_lookups',
            )
            if self._lookup_method == self.LookupMethod.Id:
                kwargs['user_id'] = ','.join(request_chunk)
            elif self._lookup_method == self.LookupMethod.Username:
                kwargs['screen_name'] = ','.join(request_chunk)

            self._tasks.append(Task(**kwargs))
