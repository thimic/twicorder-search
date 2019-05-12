#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib

from twicorder.cached_users import CachedUserCentral
from twicorder.constants import DEFAULT_EXPAND_USERS
from twicorder.queries import RequestQuery


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
        if self.config.get('full_user_mentions', DEFAULT_EXPAND_USERS):
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
        if self.config.get('full_user_mentions', DEFAULT_EXPAND_USERS):
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

