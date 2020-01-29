#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import hashlib
import json
import os
import time
import traceback
import urllib
import yaml

from datetime import datetime, timedelta

from twicorder.appdata import AppData
from twicorder.auth import AuthHandler
from twicorder.config import Config
from twicorder.constants import (
    AuthMethod,
    DEFAULT_OUTPUT_EXTENSION,
    RequestMethod,
    TW_TIME_FORMAT
)
from twicorder.rate_limits import RateLimitCentral
from twicorder.utils import write, timestamp_to_datetime

from typing import Set


class BaseQuery:
    """
    Base Query class.
    """
    name = NotImplemented
    endpoint = NotImplemented
    _max_count = NotImplemented
    _last_return_token = None
    _results_path = None
    _fetch_more_path = None
    _type = 'tweet'

    _mongo_collection = None
    _mongo_support = False

    def __init__(self, output=None, **kwargs):
        self._done = False
        self._more_results = None
        self._results = []
        self._last_id = None
        self._output = output
        self._kwargs = kwargs
        self._orig_kwargs = copy.deepcopy(kwargs)
        self._log = []

        last_return = AppData.get_last_query_id(self.uid)
        if last_return:
            self.kwargs[self.last_return_token] = last_return

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        r = f'<Query({self.name!r}, kwargs={self.kwargs!r}) at 0x{id(self):x}>'
        return r

    def __str__(self):
        return f'{self.endpoint}\n{"-" * 80}\n{yaml.dump(self.kwargs)}'

    @property
    def output(self):
        return self._output

    @property
    def last_return_token(self):
        return self._last_return_token

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def max_count(self):
        return self._max_count

    @property
    def results_path(self):
        return self._results_path

    @property
    def fetch_more_path(self):
        return self._fetch_more_path

    @property
    def type(self):
        return self._type

    @property
    def uid(self):
        raise NotImplementedError

    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, value):
        self._done = value

    @property
    def more_results(self):
        return self._more_results

    @property
    def last_id(self):
        return self._last_id

    @last_id.setter
    def last_id(self, value):
        self._last_id = value

    @property
    def results(self):
        return self._results

    @property
    def mongo_collection(self):
        if not self.mongo_support or not Config.use_mongo:
            return
        from twicorder import mongo
        collection = self._mongo_collection
        if not collection or not mongo.is_connected(collection):
            self._mongo_collection = mongo.create_collection()
        return self._mongo_collection

    @property
    def mongo_support(self) -> bool:
        """
        Whether this query supports pushing its results to MongoDB.

        Returns:
            bool: True if query supports MongoDB, else False

        """
        return self._mongo_support

    def setup(self):
        pass

    def run(self):
        raise NotImplementedError

    def finalise(self, response):
        pass

    def start(self):
        self.setup()
        response = self.run()
        self.finalise(response)
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

    def result_id(self, result: object) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (object): One single result object

        Returns:
            str: Timestamp

        """
        return f'{id(self):x}'

    def log(self, line):
        self._log.append(line)

    def fetch_log(self):
        log_data = '\n' + f' {self.endpoint} '.center(80, '=') + '\n'
        log_data += '\n'.join(self._log)
        log_data += '\n' + '=' * 80
        return log_data

    def save(self):
        """
        Save the results of the query to disk.
        """
        if not self._results or not self._output:
            return
        out_dir = os.path.join(Config.out_dir,  self._output or self.uid)
        extension = Config.out_extension or DEFAULT_OUTPUT_EXTENSION
        marker = self._results[0]
        stamp = self.result_timestamp(marker)
        uid = self.result_id(marker)
        filename = f'{stamp:%Y-%m-%d_%H-%M-%S}_{uid}{extension}'
        file_path = os.path.join(out_dir, filename)
        results_str = '\n'.join(json.dumps(r) for r in self._results)
        write(f'{results_str}\n', file_path)
        self.log(f'Wrote {len(self.results)} results to "{file_path}"')

    def push_to_mongodb(self):
        """
        Push results from query to MongoDB.
        """
        if not self.mongo_collection:
            return
        try:
            for result in self._results:
                data = copy.deepcopy(result)
                data = timestamp_to_datetime(data)
                self.mongo_collection.replace_one(
                    {'id': data['id']},
                    data,
                    upsert=True
                )
        except Exception:
            self.log(f'Unable to connect to MongoDB: {traceback.format_exc()}')
        else:
            self.log(f'Wrote {len(self.results)} tweets to MongoDB')

    def bake_ids(self):
        """
        Saves a cache of result IDs from query result to disk. In storing the
        IDs between sessions we make sure we don't save already found data.

        To prevent the disk cache growing too large, we purge IDs for results
        older than 14 days. Twitter's base search only goes back 7 days, so we
        shouldn't encounter results older than 14 days very often.
        """

        # Loading picked tweet IDs
        results = dict(AppData.get_query_objects(self.name)) or {}

        # Purging tweet IDs older than 14 days
        now = datetime.now()
        old_results = results.copy()
        results = {}
        for object_id, timestamp in old_results.items():
            dt = datetime.fromtimestamp(timestamp)
            if not now - dt > timedelta(days=14):
                results[object_id] = timestamp

        # Stores tweet IDs from result
        self._results = [r for r in self.results if r['id'] not in results]
        new_results = []
        for result in self.results:
            timestamp = self.result_timestamp(result)
            new_results.append((result['id'], int(timestamp.timestamp())))
        AppData.add_query_objects(self.name, new_results)


class BaseRequestQuery(BaseQuery):
    """
    Queries based on the requests module and the twitter API.
    """
    _base_url = 'https://api.twitter.com/1.1'
    _request_method = RequestMethod.Get
    _auth_methods = {AuthMethod.App, AuthMethod.User}
    _auth_method = AuthMethod.App

    _hash_keys = [
        'endpoint',
        '_results_path',
        '_fetch_more_path',
        '_orig_kwargs',
        '_base_url',
    ]

    def __init__(self, output=None, **kwargs):
        super().__init__(output, **kwargs)

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def request_method(self) -> RequestMethod:
        return self._request_method

    @property
    def auth_method(self) -> AuthMethod:
        return self._auth_method

    @auth_method.setter
    def auth_method(self, auth_method: AuthMethod):
        self._auth_method = auth_method

    @property
    def auth_methods(self) -> Set[AuthMethod]:
        return self._auth_methods

    @property
    def request_url(self) -> str:
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_method is RequestMethod.Get:
            if self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    @property
    def uid(self) -> str:
        hash_str = str([getattr(self, k) for k in self._hash_keys]).encode()
        return hashlib.blake2s(hash_str).hexdigest()

    def setup(self):
        # Purging logs
        self._log = []

    def run(self):

        self.log(f'URL: {self.request_url}')
        self.log(f'Method: {self.request_method.name}')
        self.log(f'Auth: {self.auth_method.name}')

        # Perform query
        attempts = 0
        while True:
            try:
                response = AuthHandler.request(
                    auth_method=self.auth_method,
                    uri=self.request_url,
                    method=self.request_method
                )
            except Exception as e:
                self.log(f'Request failed: {e}')
                attempts += 1
                time.sleep(2**attempts)
                if attempts >= 5:
                    raise
            else:
                break

        # Check query response code. Return with error message if not a
        # successful 200 code.
        if response.status != 200:
            if response.status == 429:
                self.log(f'Rate Limit in effect: {response.reason}')
                self.log(f'Message: {response.data.get("message")}')
                RateLimitCentral.insert(
                    auth_method=self.auth_method,
                    endpoint=self.endpoint,
                    limit=0,
                    remaining=0,
                    reset=datetime.now().timestamp() + 60
                )
            else:
                self.log(
                    '<{r.status}> {r.reason}: {r.data}'
                    .format(r=response)
                )
            return response
        self.log('Successful return!')

        # Search query response for additional paged results. Pronounce the
        # query done if no more pages are found.
        pagination = response.data
        if self.fetch_more_path:
            for token in self.fetch_more_path.split('.'):
                pagination = pagination.get(token, {})
            if pagination:
                self._more_results = pagination
                self.log('More pages found!')
            else:
                self._more_results = None
                self._done = True
                self.log('No more pages!')
        else:
            self._done = True

        # Extract crawled tweets from query response.
        results = response.data
        if self.results_path:
            for token in self.results_path.split('.'):
                results = results.get(token, [])
        self._results = results
        self.log(f'Result count: {len(results)}')

        # Returning crawled results
        return response


class ProductionRequestQuery(BaseRequestQuery):

    def setup(self):
        super().setup()
        # Check rate limit for query. Sleep if limits are in effect.
        limits = {}

        # Loop over available auth methods to check for rate limits
        for auth_method in self.auth_methods:
            limit = RateLimitCentral.get(auth_method, self.endpoint)
            self.log(f'{auth_method.name}: {limit}')

            # If rate limit is in effect for this method, log it and try the
            # next one
            if limit and limit.remaining == 0:
                limits[auth_method] = limit
            else:
                self._auth_method = auth_method
                break

        # If all methods were logged, rate limits are in effect everywhere.
        # Pick the auth method with the closest reset and wait.
        if self.auth_methods and len(limits) == len(self.auth_methods):
            shortest_wait = sorted(limits.items(), key=lambda x: x[1].reset)[0]
            self._auth_method = shortest_wait[0]
            sleep_time = max(shortest_wait[1].reset - time.time(), 0) + 2
            msg = (
                f'Sleeping for {sleep_time:.02f} seconds for endpoint '
                f'"{self.endpoint}".'
            )
            self.log(msg)
            time.sleep(sleep_time)

    def finalise(self, response):
        super().finalise(response)

        # Update rate limit for query
        RateLimitCentral.update(
            auth_method=self.auth_method,
            endpoint=self.endpoint,
            header=response.headers
        )

        # Save and store IDs for crawled tweets found in the query result.
        # Also record the last tweet ID found.
        if self.results:
            # Todo: Save in callback! Don't bake IDs before successful save?
            # self.save()
            pass


class TweetRequestQuery(ProductionRequestQuery):

    _mongo_support = True

    def result_timestamp(self, result):
        """
        For a given result produced by the current query, return its time stamp.

        Args:
            result (dict): One single result object

        Returns:
            datetime.datetime): Timestamp

        """
        created_at = result['created_at']
        return datetime.strptime(created_at, TW_TIME_FORMAT)

    def result_id(self, result: object) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (object): One single result object

        Returns:
            str: Timestamp

        """
        return str(result['id'])

    def finalise(self, response):
        super().finalise(response)
        self.bake_ids()
        self.log(f'Cached {self.type.title()} IDs to disk!')
        if self.results:
            if self.type == 'tweet' and self.last_id is None:
                self.last_id = self.results[0].get('id_str')

        # Cache last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self._done and self.last_id:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            AppData.set_last_query_id(self.uid, self.last_id)
