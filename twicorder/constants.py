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
