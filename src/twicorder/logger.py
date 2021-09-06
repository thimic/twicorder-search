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
        cls._logger = logging.getLogger('Twicorder')
        if Config:
            if not os.path.exists(Config.log_dir):
                os.makedirs(Config.log_dir)
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
        stream_handler.setLevel(logging.INFO)
        cls._logger.addHandler(stream_handler)

        cls._logger.setLevel(logging.INFO)

    def __new__(cls, *args, **kwargs):
        if not cls._logger:
            cls.setup()
        return cls._logger
