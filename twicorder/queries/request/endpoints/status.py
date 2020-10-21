#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable, Optional

from twicorder.appdata import AppData
from twicorder.queries import TweetRequestQuery


class StatusQuery(TweetRequestQuery):

    name = 'status'
    endpoint = '/statuses/lookup'
    result_type = TweetRequestQuery.ResultType.TweetList

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[StatusQuery], bool]] = None,
                 **kwargs):
        super().__init__(app_data, taskgen, output, max_count, stop_func, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs['trim_user'] = 'false'
        self._kwargs.update(kwargs)

    async def save(self):
        """
        Save the results of the query to disk.
        """
        for status in self.results:
            pass
        msg = f'Save for endpoint "{self.endpoint}" is not yet implemented.'
        raise NotImplementedError(msg)
