#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import hashlib
import json
import os
import requests
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
    ResultType,
    TW_TIME_FORMAT
)
from twicorder.rate_limits import RateLimitCentral
from twicorder.utils import write, timestamp_to_datetime

from typing import Set, Optional, Iterable


class BaseQuery:
    """
    Base Query class.
    """
    name = NotImplemented
    endpoint = NotImplemented
    _cursor_key = None
    _results_path = None
    _next_cursor_path = None
    _type = ResultType.Generic

    _mongo_collection = None
    _mongo_support = False

    def __init__(self, output=None, max_count=0, **kwargs):
        """
        BaseQuery constructor.

        Args:
            output (str): Output directory, relative to project directory
            max_count (int): Max results to query
            **kwargs (dict): Keyword arguments for building the query url

        """
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
        self._log = []

        last_cursor = AppData.get_last_cursor(self.uid)
        if last_cursor:
            self.kwargs[self.cursor_key] = last_cursor

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        r = f'<Query({self.name!r}, kwargs={self.kwargs!r}) at 0x{id(self):x}>'
        return r

    def __str__(self):
        return f'{self.endpoint}\n{"-" * 80}\n{yaml.dump(self.kwargs)}'

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
    def done(self) -> bool:
        """
        Whether the query is complete or not.

        Returns:
            bool: True if the query is complete, else False

        """
        return self._done

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

    @property
    def mongo_collection(self) -> Optional['pymongo.collection.Collection']:
        """
        Mongo collection tweets are ingested into, if the crawler is integrated
        with MongoDB.

        Returns:
            pymongo.collection.Collection: MongoDb collection

        """
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
        """
        Method called immediately before the query runs.
        """
        pass

    def run(self):
        """
        Method that executes main query. Use start() to execute.
        """
        raise NotImplementedError

    def finalise(self, response: requests.Response):
        """
        Method called immediately after the query runs.

        Args:
            response (requests.Response): Response to query

        """
        pass

    def start(self):
        """
        Method for executing main setup, run and finalise queries in sequence.
        """
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
        self.log(f'Wrote {len(list(self.results))} results to "{file_path}"')

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
            self.log(f'Wrote {len(list(self.results))} tweets to MongoDB')

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
        '_next_cursor_path',
        '_orig_kwargs',
        '_base_url',
    ]

    def __init__(self, output=None, max_count=0, **kwargs):
        super().__init__(output, max_count, **kwargs)

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    @property
    def base_url(self) -> str:
        """
        Base API url for all queries.

        Returns:
            str: API url

        """
        return self._base_url

    @property
    def request_method(self) -> RequestMethod:
        """
        Http request method, such as 'GET' and 'POST'.

        Returns:
            RequestMethod: Request method

        """
        return self._request_method

    @property
    def auth_method(self) -> AuthMethod:
        """
        Twitter API authentication method currently in use. Either App or User
        authentication.

        Returns:
            AuthMethod: App or User auth

        """
        return self._auth_method

    @auth_method.setter
    def auth_method(self, auth_method: AuthMethod):
        """
        Twitter API authentication method currently in use. Either App or User
        authentication.

        Args:
            auth_method (AuthMethod): App or User auth

        """
        self._auth_method = auth_method

    @property
    def auth_methods(self) -> Set[AuthMethod]:
        """
        Available Twitter API authentication methods for this query. Defaults to
        both App and User.

        Returns:
            set[AuthMethod]: Set of authentication methods

        """
        return self._auth_methods

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
            if self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    @property
    def uid(self) -> str:
        """
        Unique identifier for this query.

        Returns:
            str: Unique identifier

        """
        hash_str = str([getattr(self, k) for k in self._hash_keys]).encode()
        return hashlib.blake2s(hash_str).hexdigest()

    def setup(self):
        """
        Method called immediately before the query runs.
        """
        # Purging logs
        self._log = []

    def run(self):
        """
        Method that executes main query. Use start() to execute.
        """

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
                import traceback
                traceback.print_exc()
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
        cursor = response.data.copy()
        if self.next_cursor_path:
            for token in self.next_cursor_path.split('.'):
                cursor = cursor.get(token, {})
            if cursor:
                self._next_cursor = cursor
                self.log('More pages found!')
            else:
                self._next_cursor = None
                self._done = True
                self.log('No more pages!')
        else:
            self._done = True

        # Extract crawled tweets from query response.
        self._response_data = response.data
        results = response.data.copy()
        if self.results_path:
            for token in self.results_path.split('.'):
                results = results.get(token, [])
        self._results = results
        self._result_count += len(results)
        if self._max_count and self._result_count >= self._max_count:
            self._done = True
        self.log(f'Result count: {len(results)}')

        # Returning crawled results
        return response


class ProductionRequestQuery(BaseRequestQuery):
    """
    Base class for production queries. These are queries that should have their
    rate limits counted.
    """

    def setup(self):
        """
        Method called immediately before the query runs.
        """
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

    def finalise(self, response: requests.Response):
        """
        Method called immediately after the query runs.

        Args:
            response (requests.Response): Response to query

        """
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
    """
    Base class for queries returning tweets.
    """

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

    def result_id(self, result: dict) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (dict): One single result object

        Returns:
            str: Result ID

        """
        return str(result['id'])

    def finalise(self, response: requests.Response):
        """
        Method called immediately after the query runs.

        Args:
            response (requests.Response): Response to query

        """
        super().finalise(response)
        self.bake_ids()
        self.log(f'Cached {self.type.name} IDs to disk!')
        if self.results:
            self.last_cursor = self.results[0].get('id')

        # Cache last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self.last_cursor:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            AppData.set_last_cursor(self.uid, self.last_cursor)
