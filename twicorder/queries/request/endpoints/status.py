#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.appdata import AppData
from twicorder.queries import TweetRequestQuery


class StatusQuery(TweetRequestQuery):

    name = 'status'
    endpoint = '/statuses/lookup'

    def __init__(self, app_data: AppData, output: str = None,
                 max_count: int = 0, **kwargs):
        super().__init__(app_data, output, max_count, **kwargs)
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