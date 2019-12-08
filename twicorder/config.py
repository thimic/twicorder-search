#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import datetime
import os
import yaml

from twicorder.constants import (
    APP_DATA_TOKEN,
    DEFAULT_CONFIG_RELOAD_INTERVAL,
    DEFAULT_PROJECT_DIR,
)


class _Config(dict):
    """
    Class for reading config file. Re-checking file on disk after a set
    interval to pick up changes.
    """
    _cache_time = None

    @staticmethod
    @click.command()
    @click.option('--project-dir')
    @click.option('--output-dir')
    @click.option('--out-extension')
    @click.option('--consumer-key')
    @click.option('--consumer-secret')
    @click.option('--access-token')
    @click.option('--access-secret')
    def _read(project_dir, output_dir, out_extension,
              consumer_key, consumer_secret, access_token, access_secret):
        """
        Reading config file from disk and parsing to a dictionary using the
        yaml module. Environment variables overrides keys in the yaml file.

        Args:
            project_dir (str): Project directory
            output_dir (str): Save directory for recorded tweets
            out_extension (str): File extension for recorded tweets, i.e. '.zip'
            consumer_key (str): Twitter consumer key
            consumer_secret (str): Twitter consumer secret
            access_token (str): Twitter access token
            access_secret (str): Twitter access secret

        Returns:
            dict: Config object

        """
        if not project_dir:
            project_dir = DEFAULT_PROJECT_DIR
        config_path = os.path.join(project_dir, 'config')
        if os.path.isfile(config_path):
            with open(os.path.join(project_dir, 'config'), 'r') as stream:
                data = yaml.full_load(stream)
        else:
            data = {}
        if project_dir:
            data['project_dir'] = project_dir
        if output_dir:
            data['save_dir'] = output_dir
        if out_extension:
            data['save_extension'] = out_extension
        if consumer_key:
            data['consumer_key'] = consumer_key
        if consumer_secret:
            data['consumer_secret'] = consumer_secret
        if access_token:
            data['access_token'] = access_token
        if access_secret:
            data['access_secret'] = access_secret

        data['config_dir'] = os.path.join(data['project_dir'], 'config')
        data['preferences'] = os.path.join(
            data['config_dir'], 'preferences.yaml'
        )
        data['tasks'] = os.path.join(data['config_dir'], 'tasks.yaml')
        data['appdata_dir'] = os.path.join(data['project_dir'], 'appdata')
        data['appdata'] = os.path.join(
            data['appdata_dir'], f'{APP_DATA_TOKEN}.sql'
        )
        data['log_dir'] = os.path.join(data['project_dir'], 'logs')
        data['logs'] = os.path.join(data['log_dir'], f'{APP_DATA_TOKEN}.log')
        return data

    def _load(self):
        """
        Load config data from file or environment variables. Reload if
        reload_interval has been exceeded.
        """
        reload_interval = (
            self.get('config_reload_interval') or DEFAULT_CONFIG_RELOAD_INTERVAL
        )
        max_interval = datetime.timedelta(seconds=reload_interval)
        if (self._cache_time is None
                or datetime.datetime.now() - self._cache_time > max_interval):
            data = self._read(
                auto_envvar_prefix='TWICORDER',
                standalone_mode=False
            )
            self.update(data)
            self._cache_time = datetime.datetime.now()

    def __getitem__(self, item):
        """
        Return config attribute value for the given name. Reload config before
        returning value if reload_interval has been exceeded.

        Args:
            item (str): Config attribute name

        Returns:
            object: Config attribute value

        """
        self._load()
        return super(_Config, self).__getitem__(item)

    def __getattr__(self, item):
        """
        Return config attribute value for the given name. Reload config before
        returning value if reload_interval has been exceeded.

        Args:
            item (str): Config attribute name

        Returns:
            object: Config attribute value

        """
        self._load()
        return self.get(item)


Config = _Config()
