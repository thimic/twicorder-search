#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import httpx
import urllib

from typing import Callable, Optional

from twicorder.appdata import AppData
from twicorder.config import Config
from twicorder.constants import DEFAULT_OUTPUT_EXTENSION, RequestMethod
from twicorder.queries import ProductionRequestQuery


class FollowerIDQuery(ProductionRequestQuery):
    """
    Example for tasks.yaml:

    follower_ids:                      # Endpoint name
      - frequency: 60                  # Interval between repeating queries in minutes
        iterations: 1                  # Number of times to repeat the query, 0 means indefinitely
        output: noradio/followers/ids  # Output directory, relative to project directory
        kwargs:                        # Keyword Arguments to feed to endpoint
          user_id: 783214              # User ID to get follower IDs for
      - frequency: 60                  # Interval between repeating queries in minutes
        iterations: 1                  # Number of times to repeat the query, 0 means indefinitely
        output: noradio/followers/ids  # Output directory, relative to project directory
        kwargs:
          screen_name: noradio         # Screen name to get follower IDs for
          count: 200                   # Number of follower IDs to look up per request

    """

    name = 'follower_ids'
    endpoint = '/followers/ids'
    result_type = ProductionRequestQuery.ResultType.UserIDList
    _results_path = 'ids'
    _next_cursor_path = 'next_cursor'
    _cursor_key = 'cursor'

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[FollowerIDQuery], bool]] = None,
                 **kwargs):
        super().__init__(app_data, taskgen, output, max_count, stop_func, **kwargs)
        self._kwargs['count'] = '5000'
        self._kwargs.update(kwargs)

    @property
    def request_url(self) -> str:
        """
        Fully formatted request url constructed from base API url, end point and
        keyword arguments.

        Returns:
            str: Constructed request url

        """
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_method is RequestMethod.Get:
            if self.next_cursor:
                self.kwargs['cursor'] = self.next_cursor
            url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def result_id(self, result: int) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (object): One single result object

        Returns:
            str: Result ID

        """
        return str(result)

    async def finalise(self, response: httpx.Response):
        """
        Method called immediately after the query runs.

        Args:
            response: Response to query

        """
        await super().finalise(response)

        if self.results:
            self.last_cursor = self.response_data.get('next_cursor')

        # Cache last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self.done and self.last_cursor:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            await self.app_data.set_last_cursor(self.uid, self.last_cursor)

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
        return f'{stamp:%Y-%m-%d_%H-%M-%S}_{self.iterations:04d}{extension}'
