#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

DEFAULT_PROJECT_DIR = os.path.join(os.path.expanduser('~'), 'Twicorder')
DEFAULT_OUTPUT_EXTENSION = '.zip'

DEFAULT_CONFIG_RELOAD_INTERVAL = 15
DEFAULT_MONGO_OUTPUT = False
DEFAULT_EXPAND_USERS = False
DEFAULT_EXPAND_USERS_INTERVAL = 15

TW_TIME_FORMAT = '%a %b %d %H:%M:%S %z %Y'

REGULAR_EXTENSIONS = ['txt', 'json', 'yaml', 'twc']
COMPRESSED_EXTENSIONS = ['gzip', 'zip', 'twzip']

COMPANY = 'Zhenyael'
APP = 'Twicorder'

APP_DATA_TOKEN = 'twicorder'
