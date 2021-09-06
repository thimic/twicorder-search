#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import copy
import httpx
import json
import os
import yaml

from datetime import datetime, timedelta
from enum import Enum
from functools import partial

from twicorder.appdata import AppData
from twicorder.config import Config
from twicorder.constants import (
    DEFAULT_OUTPUT_EXTENSION,
    ResultType,
)
from twicorder.utils import write

from typing import Any, Optional, Iterable, Callable


from twicorder.logger import TwiLogger
logger = TwiLogger()


class BaseQuery:
    """
    Base Query class.
    """
    name = NotImplemented
    endpoint = NotImplemented
    result_type = NotImplemented
    _cursor_key = None
    _results_path = None
    _next_cursor_path = None
    _type = ResultType.Generic

    class ResultType(Enum):
        """
        Enum for result types.
        """
        Tweet = 'tweet'
        TweetList = 'tweet_list'
        TweetID = 'tweet_id'
        TweetIDList = 'tweet_id_list'
        User = 'user'
        UserList = 'user_list'
        UserID = 'user_list'
        UserIDList = 'user_id_list'
        RateLimit = 'rate_limit'

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[BaseQuery], bool]] = None,
                 **kwargs):
        """
        BaseQuery constructor.

        Args:
            app_data: AppData object for persistent storage between sessions
            taskgen: Name of the generator that created the task query
            output: Output directory, relative to project directory
            max_count: Max results to query
            stop_func: Custom function that takes the query as input. If
                       returning True, the query will report as done
            **kwargs: Keyword arguments for building the query url

        """
        self._app_data = app_data
        self._taskgen = taskgen
        self._done = False
        self._max_count = max_count
        self._next_cursor = None
        self._response_data = None
        self._results = []
        self._result_count = 0
        self._last_cursor = None
        self._output = output
        self._kwargs = kwargs
        self._orig_kwargs = copy.deepcopy(kwargs)
        self._iterations = 0
        self._stop_func = stop_func

        self._log = []

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        r = f'<Query({self.name!r}, kwargs={self.kwargs!r}) at 0x{id(self):x}>'
        return r

    def __str__(self):
        return f'{self.endpoint}\n{"-" * 80}\n{yaml.dump(self.kwargs)}'

    @property
    def app_data(self):
        """
        AppData object for persistent storage between sessions.
        """
        return self._app_data

    @property
    def taskgen(self) -> str:
        """
        Name of the generator that created the task query.

        Returns:
            Task generator name

        """
        return self._taskgen

    @property
    def output(self) -> Optional[str]:
        """
        Output path in which to store query data, relative to project directory.

        Returns:
            str: Output directory

        """
        return self._output

    @property
    def cursor_key(self) -> str:
        """
        Name of cursor for this query. Used to request data from the last cursor
        position on application restart.

        Returns:
            str: Cursor key

        """
        return self._cursor_key

    @property
    def kwargs(self) -> dict:
        """
        Keyword arguments used to build the Twitter query url.

        Returns:
            dict: Query arguments

        """
        return self._kwargs

    @property
    def max_count(self) -> int:
        """
        Stop query when this number of results has been reached or exceeded. To
        crawl indefinitely, set max_count to 0.

        Returns:
            int: Max result count

        """
        return self._max_count

    @property
    def iterations(self) -> int:
        """
        Number of times the query has been called while not reporting done.

        Returns:

        """
        return self._iterations

    @property
    def results_path(self) -> str:
        """
        Key for result data if result is a dictionary. Each level of the
        directory is separated by a dot.

        Examples:

            {"ids": [...], ...}                       : "ids"
            {"resources": {"users": [...], ...}, ...} : "resources.users"

        Returns:
            str: Results key path

        """
        return self._results_path

    @property
    def next_cursor_path(self) -> str:
        """
        Key in result dictionary for fetching the next page of data. Each level
        of the directory is separated by a dot.

        Examples:

            {"next_cursor": ..., ...}                       : "next_cursor"
            {"search_metadata": {"next_results": ...}, ...} : "search_metadata.next_results"

        Returns:
            str:

        """
        return self._next_cursor_path

    @property
    def type(self) -> ResultType:
        """
        Data type expected in the result, such as Tweet and User.

        Returns:
            ResultType: Result type

        """
        return self._type

    @property
    def uid(self) -> str:
        """
        Unique identifier for this query.

        Returns:
            str: Unique identifier

        """
        raise NotImplementedError

    @property
    def filename(self) -> str:
        """
        Computed file name for saving results to disk.

        Returns:
            Result file name

        """
        extension = Config.out_extension or DEFAULT_OUTPUT_EXTENSION
        marker = self._results[0]
        stamp = self.result_timestamp(marker)
        uid = self.result_id(marker)
        return f'{stamp:%Y-%m-%d_%H-%M-%S}_{uid}{extension}'

    @property
    def done(self) -> bool:
        """
        Whether the query is complete or not.

        Returns:
            bool: True if the query is complete, else False

        """
        if self._done:
            return True
        if self._stop_func:
            return self._stop_func(self)
        return False

    @done.setter
    def done(self, value: bool):
        """
        Whether the query is complete or not.

        Args:
            value (bool): Complete status

        """
        self._done = value

    @property
    def next_cursor(self) -> Optional[int]:
        """
        The next cursor, as returned by the Twitter API. If no position is set,
        the query starts at the beginning.

        Returns:
            int: Cursor ID

        """
        return self._next_cursor

    @property
    def last_cursor(self) -> Optional[int]:
        """
        The cursor for the last returned result object. This is cached so a
        cursor can be included for some end points that otherwise don't provide
        cursors.

        Returns:
            int: Cursor ID

        """
        return self._last_cursor

    @last_cursor.setter
    def last_cursor(self, value: int):
        """
        The cursor for the last returned result object. This is cached so a
        cursor can be included for some end points that otherwise don't provide
        cursors.

        Args:
            value (int): Cursor ID

        """
        self._last_cursor = value

    @property
    def results(self) -> Iterable:
        """
        Result set for this query.

        Returns:
            object: Result for query

        """
        return self._results

    @property
    def result_count(self) -> int:
        """
        Total results returned by this query.

        Returns:
            int: Total result count

        """
        return self._result_count

    @property
    def response_data(self) -> object:
        """
        Raw response data object.

        Returns:
            object: Response data

        """
        return self._response_data

    async def setup(self):
        """
        Method called immediately before the query runs.
        """
        last_cursor = await self.app_data.get_last_cursor(self.uid)
        if last_cursor:
            self.kwargs[self.cursor_key] = last_cursor

    async def run(self):
        """
        Method that executes main query. Use start() to execute.
        """
        raise NotImplementedError

    async def finalise(self, response: httpx.Response):
        """
        Method called immediately after the query runs.

        Args:
            response: Response to query

        """
        pass

    async def start(self):
        """
        Method for executing main setup, run and finalise queries in sequence.
        """
        await self.setup()
        response = await self.run()
        self._iterations += 1
        await self.finalise(response)
        return self.results

    def result_timestamp(self, result) -> datetime:
        """
        For a given result produced by the current query, return its time stamp.

        Args:
            result (dict): One single result object

        Returns:
            datetime.datetime: Timestamp

        """
        return datetime.utcnow()

    def result_id(self, result: Any) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (object): One single result object

        Returns:
            str: Result ID

        """
        return f'{id(self):x}'

    def log(self, line: str):
        """
        Adds the given line to a list of logs for this query. This way logs from
        separate threads can be printed sequentially in the main thread.

        Args:
            line (str): Line to log

        """
        self._log.append(line)

    def fetch_log(self) -> str:
        """
        Formats and returns the query's logged lines as one contained chunk.

        Returns:
            str: Formatted log

        """
        log_data = '\n' + f' {self.endpoint} '.center(80, '=') + '\n'
        log_data += '\n'.join(self._log)
        log_data += '\n' + '=' * 80
        return log_data

    async def save(self):
        """
        Save the results of the query to disk.
        """
        if not self._results or not self._output:
            return
        loop = asyncio.get_event_loop()
        out_dir = os.path.join(Config.out_dir,  self._output or self.uid)
        file_path = os.path.join(out_dir, self.filename)
        results_str = '\n'.join(json.dumps(r) for r in self._results)
        await loop.run_in_executor(
            None,
            partial(write, f'{results_str}\n', file_path)
        )
        self.log(f'Wrote {len(list(self.results))} results to "{file_path}"')

    async def bake_ids(self):
        """
        Saves a cache of result IDs from query result to disk. In storing the
        IDs between sessions we make sure we don't save already found data.

        To prevent the disk cache growing too large, we purge IDs for results
        older than 14 days. Twitter's base search only goes back 7 days, so we
        shouldn't encounter results older than 14 days very often.
        """

        # Loading pickled tweet IDs
        results = dict(await self.app_data.get_query_objects(self.name)) or {}

        # Purging tweet IDs older than 14 days
        now = datetime.utcnow()
        old_results = results.copy()
        results = {}
        for object_id, timestamp in old_results.items():
            dt = datetime.fromtimestamp(timestamp)
            if not now - dt > timedelta(days=14):
                results[object_id] = timestamp

        # Purging duplicates from results
        self._results = [r for r in self.results if r['id'] not in results]

        # Stores tweet IDs from result
        new_results = []
        for result in self.results:
            new_results.append((result['id'], int(now.timestamp())))
        await self.app_data.add_query_objects(self.name, new_results)
