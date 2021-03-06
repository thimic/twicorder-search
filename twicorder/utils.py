#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import sys

from datetime import datetime
from gzip import GzipFile
from logging import StreamHandler
from threading import Lock

from logging.handlers import RotatingFileHandler

from twicorder.config import Config
from twicorder.constants import (
    COMPRESSED_EXTENSIONS,
    DEFAULT_APP_DATA_CONNECTION_TIMEOUT,
    REGULAR_EXTENSIONS,
    TW_TIME_FORMAT,
)
from twicorder.project_manager import ProjectManager


class TwiLogger:

    _logger = None

    @classmethod
    def setup(cls):
        cls._logger = logging.getLogger('Twicorder')
        file_handler = RotatingFileHandler(
            ProjectManager.logs,
            maxBytes=1024**2 * 10,
            backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s: [%(levelname)s] %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.WARNING)
        cls._logger.addHandler(file_handler)

        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        cls._logger.addHandler(stream_handler)

        cls._logger.setLevel(logging.DEBUG)

    def __new__(cls, *args, **kwargs):
        if not cls._logger:
            cls.setup()
        return cls._logger


def auto_commit(func):
    def func_wrapper(self, *args, **kwargs):
        with self._conn:
            func(self, *args, **kwargs)
    return func_wrapper


class AppData:
    """
    Class for reading and writing AppData to be used between sessions.
    """

    _config = Config.get()
    _timeout = (
        _config.get('appdata_connection_timeout') or
        DEFAULT_APP_DATA_CONNECTION_TIMEOUT
    )
    _con = sqlite3.connect(
        ProjectManager.app_data,
        check_same_thread=False,
        timeout=float(_timeout)
    )
    _lock = Lock()

    def __del__(self):
        self._con.close()

    @classmethod
    def _make_query_table(cls, name):
        with cls._lock, cls._con as con:
            con.execute(
                f'''
                CREATE TABLE IF NOT EXISTS [{name}] (
                    tweet_id INTEGER PRIMARY KEY,
                    timestamp INTEGER NOT NULL
                )
                '''
            )

    @classmethod
    def _make_last_id_table(cls):
        with cls._lock, cls._con as con:
            con.execute(
                '''
                CREATE TABLE IF NOT EXISTS queries_last_id (
                    query_hash TEXT PRIMARY KEY,
                    tweet_id INTEGER NOT NULL
                )
                '''
            )

    @classmethod
    def add_query_tweet(cls, query_name, tweet_id, timestamp):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            con.execute(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                (tweet_id, timestamp)
            )

    @classmethod
    def add_query_tweets(cls, query_name, tweets):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            con.executemany(
                f'''
                INSERT OR REPLACE INTO {query_name} VALUES (
                    ?, ?
                )
                ''',
                tweets
            )

    @classmethod
    def get_query_tweets(cls, query_name):
        cls._make_query_table(query_name)
        with cls._lock, cls._con as con:
            cursor = con.cursor()
            cursor.execute(
                f'''
                SELECT DISTINCT
                    tweet_id, timestamp
                FROM
                    {query_name}
                '''
            )
            return cursor.fetchall()

    @classmethod
    def set_last_query_id(cls, query_hash, tweet_id):
        cls._make_last_id_table()
        with cls._lock, cls._con as con:
            con.execute(
                '''
                INSERT OR REPLACE INTO queries_last_id VALUES (
                    ?, ?
                )
                ''',
                (query_hash, tweet_id)
            )

    @classmethod
    def get_last_query_id(cls, query_hash):
        cls._make_last_id_table()
        with cls._lock, cls._con as con:
            cursor = con.cursor()
            cursor.execute(
                '''
                SELECT
                DISTINCT
                    tweet_id
                FROM
                    queries_last_id
                WHERE
                    query_hash=?
                ''',
                (query_hash,)
            )
            result = cursor.fetchone()
        if not result:
            return
        return result[0]


def twopen(filename, mode='r'):
    """
    Replacement method for Python's build-in open. Adds the option to handle
    compressed files.

    Args:
        filename (str): Path to file
        mode (str): Open mode

    Returns:
        TextIOWrapper / GzipFile: File object

    Raises:
        IOError: If extension is unknown.

    """
    filename = os.path.expanduser(filename)
    dirname = os.path.dirname(filename)
    if mode in ('a', 'w') and not os.path.isdir(dirname):
        os.makedirs(dirname)
    ext = os.path.splitext(filename)[-1].strip('.')
    if ext in REGULAR_EXTENSIONS:
        return open(file=filename, mode=mode)
    elif ext in COMPRESSED_EXTENSIONS:
        return GzipFile(filename=filename, mode=mode)
    else:
        raise IOError('Unrecognised format: {}'.format(ext))


def read(filename):
    """
    Reading the file for a given path.

    Args:
        filename (str): Path to file to read

    Returns:
        str: File data

    """
    with twopen(filename=filename, mode='r') as file_object:
        data = file_object.read()
        if isinstance(file_object, GzipFile):
            data = data.decode('utf-8')
        return data


def readlines(filename):
    """
    Reading the file for a given path.

    Args:
        filename (str): Path to file to read

    Returns:
        str: File data

    """
    with twopen(filename=filename, mode='r') as file_object:
        data = file_object.readlines()
        if isinstance(file_object, GzipFile):
            data = [d.decode('utf-8') for d in data]
        return data


def write(data, filename, mode='a'):
    """
    Appending data to the given file.

    Args:
        data (str): Data to append to the given file
        filename (str): Path to file to write
        mode (str): File stream mode ('a'. 'w' etc)

    """
    with twopen(filename=filename, mode=mode) as file_object:
        if isinstance(file_object, GzipFile):
            file_object.write(data.encode('utf-8'))
            return
        file_object.write(data)


def message(title='Warning', body='', width=80):
    """
    Prints a formatted message based on input

    Args:
        title (str): Title of the message
        body (str): Message body
        width (int): Message line width

    """
    header = ' {} '.format(title).center(width, '=')
    footer = '=' * width
    text = (
        '\n'
        '{}\n'
        '\n'
        '{}\n'
        '\n'
        '{}\n'
        '\n'
    )
    print(text.format(header, body, footer))


def collect_key_values(key, data):
    """
    Builds a list of values for all keys matching the given "key" in a nested
    dictionary.

    Args:
        key (object): Dictionary key to search for
        data (dict): Nested data dict

    Returns:
        list: List of values for given key

    """
    values = []
    for k, v in data.items():
        if k == key:
            values.append(v)
            continue
        if isinstance(v, dict):
            values += collect_key_values(key, v)
    return values


def flatten(l):
    """
    Flattens a nested list

    Args:
        l (list): Nested list

    Returns:
        list: Flattened list

    """
    return [item for sublist in l for item in sublist]


def str_to_date(text):
    """
    Turns a time stamp represented as a string into a datetime object.

    Args:
        text (str): Time stamp

    Returns:
        datetime.datetime: Time stamp as datetime object

    """
    return datetime.strptime(text, TW_TIME_FORMAT)


def timestamp_to_datetime(data):
    """
    Traverse dictionary and convert all instances of time stamp strings into
    datetime objects.

    Args:
        data (dict): Tweet dictionary

    Returns:
        dict: Updated tweet dictionary

    """
    for key, value in data.items():
        if key in ['created_at', 'recorded_at'] and isinstance(value, str):
            data[key] = datetime.strptime(value, TW_TIME_FORMAT)
        elif isinstance(value, dict):
            data[key] = timestamp_to_datetime(value)
        elif isinstance(value, list):
            data[key] = [
                timestamp_to_datetime(v) for v in value if isinstance(v, dict)
            ]
    return data


def stream_to_search(data):
    """
    Conform tweet dictionaries collected from the streaming API to the format of
    tweets collected from the search API.

    Args:
        data (dict): Tweet dictionary

    Returns:
        dict: Updated tweet dictionary

    """
    extended_tweet = data.get('extended_tweet')
    if extended_tweet:
        data.pop('extended_tweet')
        data.update(extended_tweet)
        data['truncated'] = False
        data.pop('text')
    else:
        if data.get('text'):
            data['full_text'] = data.pop('text')
    for key, value in data.items():
        if key in ['retweeted_status', 'quoted_status']:
            data[key] = stream_to_search(value)
    return data
