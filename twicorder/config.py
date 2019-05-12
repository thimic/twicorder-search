#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import yaml

from twicorder import NoConfigException
from twicorder.constants import DEFAULT_CONFIG_RELOAD_INTERVAL
from twicorder.project_manager import ProjectManager


class Config:
    """
    Class for reading config file. Re-checking file on disk after a set
    interval to pick up changes.
    """

    _cache = None
    _cache_time = None
    _last_path = None

    @classmethod
    def _load(cls):
        """
        Reading config file from disk and parsing to a dictionary using the
        yaml module.

        Returns:
            dict: Config object

        """
        if not os.path.isfile(ProjectManager.preferences):
            raise NoConfigException
        with open(ProjectManager.preferences, 'r') as stream:
            config = yaml.full_load(stream)
        return config

    @classmethod
    def get(cls):
        """
        Reads config file from disk if no config object has been loaded or if
        the available config object has expired. Otherwise serving up a cached
        config object.

        Returns:
            dict: Config object

        """
        if not cls._cache or ProjectManager.preferences != cls._last_path:
            cls._cache = cls._load()
            cls._cache_time = datetime.datetime.now()
            return cls._cache
        reload_interval = (
            cls._cache['config_reload_interval'] or
            DEFAULT_CONFIG_RELOAD_INTERVAL
        )
        max_interval = datetime.timedelta(seconds=reload_interval)
        if datetime.datetime.now() - cls._cache_time > max_interval:
            cls._cache = cls._load()
            cls._cache_time = datetime.datetime.now()
        return cls._cache
