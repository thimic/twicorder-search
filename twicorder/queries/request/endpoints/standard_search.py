#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib

from twicorder.appdata import AppData
from twicorder.constants import RequestMethod
from twicorder.queries import TweetRequestQuery


class StandardSearchQuery(TweetRequestQuery):

    name = 'free_search'
    endpoint = '/search/tweets'
    _cursor_key = 'since_id'
    _results_path = 'statuses'
    _next_cursor_path = 'search_metadata.next_results'

    def __init__(self, app_data: AppData, output: str = None,
                 max_count: int = 0, **kwargs):
        super().__init__(app_data, output, max_count, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 100
        self._kwargs['include_entities'] = 'true'
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
        if self.request_method == RequestMethod.Get:
            if self.next_cursor:
                url += self.next_cursor
                # API bug: 'search_metadata.next_results' does not include
                # 'tweet_mode'. Adding it back in manually.
                if 'tweet_mode=extended' not in url:
                    url += '&tweet_mode=extended'
            elif self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url
