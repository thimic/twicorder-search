#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import httpx
import urllib

from datetime import datetime
from typing import Callable, Optional

from twicorder.appdata import AppData
from twicorder.constants import RequestMethod
from twicorder.queries import TweetRequestQuery


class TimelineQuery(TweetRequestQuery):
    """
    Example for tasks.yaml:

    user_timeline:                 # Endpoint name
      - frequency: 15              # Interval between repeating queries in minutes
        iterations: 1              # Number of times to repeat the query, 0 means indefinitely
        output: "github/timeline"  # Output directory, relative to project directory
        kwargs:                    # Keyword Arguments to feed to endpoint
          screen_name: "github"    # Screen name to look up timeline for
      - frequency: 15
        iterations: 0
        output: "github/timeline"
        kwargs:
          screen_name: "nasa"

    """

    name = 'user_timeline'
    endpoint = '/statuses/user_timeline'
    result_type = TweetRequestQuery.ResultType.TweetList
    _cursor_key = 'since_id'

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[TimelineQuery], bool]] = None,
                 **kwargs):
        super().__init__(app_data, taskgen, output, max_count, stop_func, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 200
        self._kwargs['trim_user'] = 'false'
        self._kwargs['exclude_replies'] = 'false'
        self._kwargs['include_rts'] = 'true'
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
                self.kwargs['max_id'] = self.next_cursor
            url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    async def run(self):
        """
        Method that executes main query. Use start() to execute.
        """
        response = await super().run()
        self.done = False
        if not self.results:
            self.done = True
            return response
        self._next_cursor = self.results[-1]['id_str']
        last_return = self.kwargs.get('max_id')
        if last_return and int(self._next_cursor) >= int(last_return):
            self.done = True
        return response

    async def finalise(self, response: httpx.Response):
        await super().finalise(response)
        if not self.done:
            return

        task_id = self.kwargs.get('user_id', self.kwargs.get('screen_name'))
        if not task_id:
            return
        timestamp = int(datetime.utcnow().timestamp())
        await self.app_data.add_taskgen_id(self.taskgen, task_id, timestamp)
