#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import urllib

from datetime import datetime, timedelta

from twicorder.cached_users import CachedUserCentral
from twicorder.config import Config
from twicorder.constants import DEFAULT_EXPAND_USERS, DEFAULT_OUTPUT_EXTENSION
from twicorder.queries import RequestQuery, UserBaseQuery
from twicorder.utils import AppData, write


class UserLookupQuery(UserBaseQuery):

    name = 'user_lookups'
    endpoint = '/users/lookup'

    def __init__(self, output=None, **kwargs):
        super(UserBaseQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)


class FollowerIDQuery(UserBaseQuery):

    name = 'follower_ids'
    endpoint = '/followers/ids'
    _results_path = 'ids'
    _fetch_more_path = 'next_cursor'

    def __init__(self, output=None, **kwargs):
        super(UserBaseQuery, self).__init__(output, **kwargs)
        self._kwargs['count'] = '5000'
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                self.kwargs['cursor'] = self.more_results
            url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def bake_ids(self):
        """
        Saves a cache of user IDs from query result to disk. In storing the IDs
        between sessions, we ensure crawled data is not lost between sessions.

        To prevent the disk cache growing too large, we purge IDs for users
        crawled more than 14 days ago.
        """

        # Loading picked tweet IDs
        users = dict(AppData.get_user_ids(self.name)) or {}

        # Purging tweet IDs older than 14 days
        now = datetime.now()
        old_users = users.copy()
        users = {}
        for user_id, timestamp in old_users.items():
            dt = datetime.fromtimestamp(timestamp)
            if not now - dt > timedelta(days=14):
                users[user_id] = timestamp

        # Stores tweet IDs from result
        self._results = [u for u in self.results if u not in users]
        new_users = []
        for result in self.results:
            dt = datetime.utcnow()
            timestamp = int(dt.timestamp())
            new_users.append((result, timestamp))
        AppData.add_user_ids(self.name, new_users)

    def save(self):
        if not self._results or not self._output:
            return
        out_dir = os.path.join(
            Config.out_dir,
            self._output or self.uid
        )
        extension = Config.out_extension or DEFAULT_OUTPUT_EXTENSION
        marker = self._results[0]
        stamp = datetime.utcnow()
        filename = f'{stamp:%Y-%m-%d_%H-%M-%S}_{marker}{extension}'
        file_path = os.path.join(out_dir, filename)
        results_str = '\n'.join(json.dumps(r) for r in self._results)
        write(f'{results_str}\n', file_path)
        self.log(f'Wrote {len(self.results)} tweets to "{file_path}"')


class StatusQuery(RequestQuery):

    name = 'status'
    endpoint = '/statuses/lookup'

    def __init__(self, output=None, **kwargs):
        super(StatusQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs['trim_user'] = 'false'
        self._kwargs.update(kwargs)

    def save(self):
        for status in self.results:
            pass
        msg = f'Save for endpoint "{self.endpoint}" is not yet implemented.'
        raise NotImplementedError(msg)


class TimelineQuery(RequestQuery):

    name = 'user_timeline'
    endpoint = '/statuses/user_timeline'
    _last_return_token = 'since_id'

    def __init__(self, output=None, **kwargs):
        super(TimelineQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 200
        self._kwargs['trim_user'] = 'false'
        self._kwargs['exclude_replies'] = 'false'
        self._kwargs['include_rts'] = 'true'
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                self.kwargs['max_id'] = self.more_results
            url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def run(self):
        super(TimelineQuery, self).run()
        self.done = False
        if not self.results:
            self.done = True
            return
        self._more_results = self.results[-1]['id_str']
        last_return = self.kwargs.get('max_id')
        if last_return and int(self._more_results) >= int(last_return):
            self.done = True

    def save(self):
        if Config.full_user_mentions or DEFAULT_EXPAND_USERS:
            self.log('Expanding user mentions!')
            CachedUserCentral.expand_user_mentions(self.results)
        super(TimelineQuery, self).save()


class StandardSearchQuery(RequestQuery):

    name = 'free_search'
    endpoint = '/search/tweets'
    _last_return_token = 'since_id'
    _results_path = 'statuses'
    _fetch_more_path = 'search_metadata.next_results'

    def __init__(self, output=None, **kwargs):
        super(StandardSearchQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 100
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                url += self.more_results
                # API bug: 'search_metadata.next_results' does not include
                # 'tweet_mode'. Adding it back in manually.
                if 'tweet_mode=extended' not in url:
                    url += '&tweet_mode=extended'
            elif self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def save(self):
        if Config.full_user_mentions or DEFAULT_EXPAND_USERS:
            self.log('Expanding user mentions!')
            CachedUserCentral.expand_user_mentions(self.results)
        super(StandardSearchQuery, self).save()


class FullArchiveGetQuery(RequestQuery):

    name = 'fullarchive_get'
    endpoint = '/tweets/search/fullarchive/production'
    _fetch_more_path = 'next'


class FullArchivePostQuery(RequestQuery):

    name = 'fullarchive_post'
    endpoint = '/tweets/search/fullarchive/production'
    _fetch_more_path = 'next'
    _request_type = 'post'
    _token_auth = True


class FriendsList(RequestQuery):

    name = 'friends_list'
    endpoint = '/friends/list'


class RateLimitStatusQuery(RequestQuery):

    name = 'rate_limit_status'
    endpoint = '/application/rate_limit_status'


if __name__ == '__main__':
    query = FollowerIDQuery(output='~/Desktop', screen_name='github')
