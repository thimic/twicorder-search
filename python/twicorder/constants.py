#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os

THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
CONFIG_DIR = os.path.join(os.sep.join(THIS_DIR.split(os.sep)[:-2]), 'config')
USER_DIR = os.path.expanduser('~/.twicorder')
TW_TIME_FORMAT = '%a %b %d %H:%M:%S %z %Y'

REGULAR_EXTENSIONS = ['txt', 'json', 'yaml', 'twc']
COMPRESSED_EXTENSIONS = ['gzip', 'zip', 'twzip']

COMPANY = 'Zhenyael'
APP = 'Twicorder'

APP_DATA_TOKEN = 'twicorder'
