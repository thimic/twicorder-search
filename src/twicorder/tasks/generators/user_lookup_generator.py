#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Set, Tuple

from twicorder import NoTasksException
from twicorder.appdata import AppData
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

    def __init__(self, app_data: AppData, name_pattern: str, delimiter: str = '\n',
                 lookup_method: str = 'id'):
        """
        Entry point for UserLookupTaskGenerator.

        Args:
            app_data: AppData object for persistent storage between sessions
            name_pattern: Glob name pattern
            delimiter: User ID/name delimiter. Defaults to new line.
            lookup_method: "id" if looking up user ids or "username" if looking
                           up user names

        """
        super().__init__(app_data=app_data)
        self._name_pattern = name_pattern
        self._delimiter = delimiter
        self._lookup_method = self.LookupMethod(lookup_method)

    async def fetch(self):
        """
        Method to generate tasks. Should populate UserLookupTaskGenerator._tasks.
        """
        users: Set[str] = set()

        for filepath in Path('/').glob(self._name_pattern.lstrip('/')):
            users.update(filepath.read_text().splitlines())

        if not users:
            msg = (
                f'Found no files containing usernames or IDs for name pattern '
                f'{self._name_pattern!r}.'
            )
            raise NoTasksException(msg)

        # Remove already crawled users
        existing: Tuple[Tuple[str, int]] = await self._app_data.get_taskgen_ids(self.name)
        existing_users = {e[0] for e in existing}
        users = users.difference(existing_users)

        if self._lookup_method == self.LookupMethod.Id:
            sorted_users = sorted(users, key=lambda x: int(x))
        else:
            sorted_users = sorted(users)

        users_per_query = 100
        request_chunks = [
            sorted_users[i:i + users_per_query]
            for i in range(0, len(sorted_users), users_per_query)
        ]
        for request_chunk in request_chunks:
            kwargs = dict(
                name='user_lookups',
                taskgen=self.name,
                frequency=10000,
                iterations=1,
                output='user_lookups',
            )
            if self._lookup_method == self.LookupMethod.Id:
                kwargs['user_id'] = ','.join(request_chunk)
            elif self._lookup_method == self.LookupMethod.Username:
                kwargs['screen_name'] = ','.join(request_chunk)

            self._tasks.append(Task(**kwargs))
