#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from enum import Enum


class AuthMethod(Enum):
    """
    Enum with authentication options for queries.
    """
    App = 0
    User = 1


class RequestMethod(Enum):
    """
    Enum with request method for queries.
    """
    Get = 'get'
    Post = 'post'


class ResultType(Enum):
    """
    Enum with result types for queries.
    """
    Generic = 0
    Tweet = 1
    User = 2


API_BASE_URL = 'https://api.twitter.com/1.1'
TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'

DEFAULT_PROJECT_DIR = os.getcwd()
DEFAULT_OUTPUT_EXTENSION = '.zip'

DEFAULT_EXPAND_USERS = False
DEFAULT_EXPAND_USERS_INTERVAL = 15

DEFAULT_TASK_FREQUENCY = 15
DEFAULT_TASK_ITERATIONS = 0
DEFAULT_TASK_KWARGS = {}

TW_TIME_FORMAT = '%a %b %d %H:%M:%S %z %Y'

REGULAR_EXTENSIONS = ['txt', 'json', 'yaml', 'twc']
COMPRESSED_EXTENSIONS = ['gzip', 'zip', 'twzip']

COMPANY = 'Zhenyael'
APP = 'Twicorder'

APP_DATA_TOKEN = 'twicorder'
DEFAULT_APP_DATA_CONNECTION_TIMEOUT = 5.0
