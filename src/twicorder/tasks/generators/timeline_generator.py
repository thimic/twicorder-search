#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Optional, Set, Tuple

from twicorder import NoTasksException
from twicorder.appdata import AppData
from twicorder.constants import TW_TIME_FORMAT
from twicorder.queries import BaseQuery
from twicorder.tasks.task import Task
from twicorder.tasks.generators.base_generator import BaseTaskGenerator


class UserTimelineTaskGenerator(BaseTaskGenerator):
    """
    User timeline task generator. Generates a set of TwiCorder tasks to look up
    user timeline tweets on fetch() based on files matching the given name
    pattern. The files specified by the pattern should contain delimited Twitter
    user IDs or screen names in plain text format.
    """

    class LookupMethod(Enum):
        Id = 'id'
        Username = 'username'

    name = 'user_timeline'

    def __init__(self, app_data: AppData, name_pattern: str,
                 delimiter: str = '\n', lookup_method: str = 'id',
                 max_requests: Optional[int] = None,
                 max_age: Optional[int] = None):
        """
        Entry point for UserTimelineTaskGenerator.

        Args:
            app_data: AppData object for persistent storage between sessions
            name_pattern: Glob name pattern
            delimiter: User ID/name delimiter. Defaults to new line.
            lookup_method: "id" if looking up user ids or "username" if looking
                           up user names
            max_requests: Max number of requests permitted before the task is
                          considered done.
            max_age: Max age in days for a tweet before the query should be
                     considered done

        """
        super().__init__(app_data=app_data)

        if max_requests and max_age:
            raise ValueError(
                'Supplying max_requests and max_age at the same time is not '
                'supported.'
            )

        self._name_pattern = name_pattern
        self._delimiter = delimiter
        self._lookup_method = self.LookupMethod(lookup_method)
        self._max_requests = int(max_requests) if max_requests else None
        self._max_age = timedelta(days=int(max_age)) if max_age else None

    @staticmethod
    def max_age_func(max_age: timedelta, query: BaseQuery) -> bool:
        """
        Queries will be considered done if provided with a stop function that
        returns True.

        Returns True if the oldest tweet in the result set is older than the
        given time delta.

        Args:
            max_age: Max age for a tweet before the query should be considered
                     done
            query: Query object to evaluate

        Returns:
            True if the oldest tweet in the result set is older than max_age

        """
        if not query.results:
            return False
        last_result = query.results[-1]
        created_at_str = last_result.get('created_at')
        if not created_at_str:
            return False
        created_at = datetime.strptime(created_at_str, TW_TIME_FORMAT)
        if datetime.now(timezone.utc) - created_at > max_age:
            return True
        return False

    @staticmethod
    def max_requests_func(max_requests: int, query: BaseQuery) -> bool:
        """
        Queries will be considered done if provided with a stop function that
        returns True.

        Returns True if maximum queries has been exceeded.

        Args:
            max_requests: Maximum number of requests/pages to process per query
            query: Query object to evaluate

        Returns:
            True if maximum requests for the query has been exceeded

        """
        return query.iterations >= max_requests

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

        for user in sorted_users:
            kwargs = dict(
                name='user_timeline',
                taskgen=self.name,
                frequency=10000,
                iterations=1,
                output=f'user_timelines/{user}',
            )
            if self._lookup_method == self.LookupMethod.Id:
                kwargs['user_id'] = user
            elif self._lookup_method == self.LookupMethod.Username:
                kwargs['screen_name'] = user

            task = Task(**kwargs)
            if self._max_requests:
                task.stop_func = partial(
                    self.max_requests_func,
                    self._max_requests
                )
            if self._max_age:
                task.stop_func = partial(
                    self.max_age_func,
                    self._max_age
                )

            self._tasks.append(task)
