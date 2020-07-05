#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys

from logging import StreamHandler

from logging.handlers import RotatingFileHandler

from twicorder.config import Config


class TwiLogger:

    _logger = None

    @classmethod
    def setup(cls):
        if not os.path.exists(Config.log_dir):
            os.makedirs(Config.log_dir)
        cls._logger = logging.getLogger('Twicorder')
        file_handler = RotatingFileHandler(
            Config.logs,
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