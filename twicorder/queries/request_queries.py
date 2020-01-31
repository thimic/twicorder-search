#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import urllib

from twicorder.appdata import AppData
from twicorder.cached_users import CachedUserCentral
from twicorder.config import Config
from twicorder.constants import DEFAULT_EXPAND_USERS, RequestMethod
from twicorder.queries import (
    BaseRequestQuery,
    ProductionRequestQuery,
    TweetRequestQuery
)


class UserLookupQuery(ProductionRequestQuery):
    """
    Example for tasks.yaml:

    user_lookups:                          # Endpoint name
      - frequency: 60                      # Interval between repeating queries in minutes
        iterations: 1                      # Number of times to repeat the query, 0 means indefinitely
        output: twitter/followers/users    # Output directory, relative to project directory
        kwargs:                            # Keyword Arguments to feed to endpoint
          user_id: 783214,6253282          # Comma separated list of user IDs, max 100
          include_entities: false          # Include entities node with statuses
      - frequency: 60                      # Interval between repeating queries in minutes
        iterations: 1                      # Number of times to repeat the query, 0 means indefinitely
        output: twitter/followers/users    # Output directory, relative to project directory
        kwargs:
          screen_name: twitterapi,twitter  # Comma separated list of screen names, max 100

    """

    name = 'user_lookups'
    endpoint = '/users/lookup'

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, max_count, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    def finalise(self, response: requests.Response):
        """
        Method called immediately after the query runs.

        Args:
            response (requests.Response): Response to query

        """
        super().finalise(response)
        self.bake_ids()
        self.log(f'Cached {self.type.name} IDs to disk!')


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
    _results_path = 'ids'
    _next_cursor_path = 'next_cursor'
    _cursor_key = 'cursor'

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, max_count, **kwargs)
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

    def result_id(self, result: object) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (object): One single result object

        Returns:
            str: Result ID

        """
        return str(result)

    def finalise(self, response: requests.Response):
        """
        Method called immediately after the query runs.

        Args:
            response (requests.Response): Response to query

        """
        super().finalise(response)

        if self.results:
            self.last_cursor = self.response_data.get('next_cursor')

        # Cache last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self._done and self.last_cursor:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            AppData.set_last_cursor(self.uid, self.last_cursor)


class StatusQuery(TweetRequestQuery):

    name = 'status'
    endpoint = '/statuses/lookup'

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, max_count, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs['trim_user'] = 'false'
        self._kwargs.update(kwargs)

    def save(self):
        """
        Save the results of the query to disk.
        """
        for status in self.results:
            pass
        msg = f'Save for endpoint "{self.endpoint}" is not yet implemented.'
        raise NotImplementedError(msg)


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
    _cursor_key = 'since_id'

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, **kwargs)
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

    def run(self):
        """
        Method that executes main query. Use start() to execute.
        """
        response = super().run()
        self.done = False
        if not self.results:
            self.done = True
            return response
        self._more_results = self.results[-1]['id_str']
        last_return = self.kwargs.get('max_id')
        if last_return and int(self._more_results) >= int(last_return):
            self.done = True
        return response

    def save(self):
        """
        Save the results of the query to disk.
        """
        if Config.full_user_mentions or DEFAULT_EXPAND_USERS:
            self.log('Expanding user mentions!')
            CachedUserCentral.expand_user_mentions(self.results)
        super(TimelineQuery, self).save()


class StandardSearchQuery(TweetRequestQuery):

    name = 'free_search'
    endpoint = '/search/tweets'
    _cursor_key = 'since_id'
    _results_path = 'statuses'
    _next_cursor_path = 'search_metadata.next_results'

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, max_count, **kwargs)
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

    def save(self):
        """
        Save the results of the query to disk.
        """
        if Config.full_user_mentions or DEFAULT_EXPAND_USERS:
            self.log('Expanding user mentions!')
            CachedUserCentral.expand_user_mentions(self.results)
        super(StandardSearchQuery, self).save()


class FullArchiveGetQuery(TweetRequestQuery):

    name = 'fullarchive_get'
    endpoint = '/tweets/search/fullarchive/production'
    _next_cursor_path = 'next'


class FullArchivePostQuery(TweetRequestQuery):

    name = 'fullarchive_post'
    endpoint = '/tweets/search/fullarchive/production'
    _next_cursor_path = 'next'
    _request_method = RequestMethod.Post


class FriendsList(ProductionRequestQuery):

    name = 'friends_list'
    endpoint = '/friends/list'


class RateLimitStatusQuery(BaseRequestQuery):

    name = 'rate_limit_status'
    endpoint = '/application/rate_limit_status'


if __name__ == '__main__':
    query = FollowerIDQuery(output='~/Desktop', screen_name='github')
