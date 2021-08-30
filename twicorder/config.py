#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from typing import List, Optional, Tuple

from twicorder.constants import (
    APP_DATA_TOKEN,
    DEFAULT_APP_DATA_CONNECTION_TIMEOUT,
    DEFAULT_EXPAND_USERS_INTERVAL,
    DEFAULT_OUTPUT_EXTENSION,
    DEFAULT_PROJECT_DIR
)


Config = None


class _Config:

    def __init__(self, consumer_key: str, consumer_secret: str,
                 access_token: str, access_secret: str, project_dir: str,
                 out_dir: str, out_extension: str, task_file: str,
                 full_user_mentions: bool, user_lookup_interval: int,
                 appdata_token: str, appdata_timeout: float,
                 task_gen: Optional[List[Tuple[str, str]]],
                 remove_duplicates: bool):
        """
        Gets config attributes from command line arguments or environment
        variables.

        Environment variables are prefixed with "TWICORDER" and otherwise match
        upper cased versions of command line arguments. "--project-dir" becomes
        "TWICORDER_PROJECT_DIR" for instance.

        Args:
            consumer_key (str): Twitter consumer key
            consumer_secret (str): Twitter consumer secret
            access_token (str): Twitter access token
            access_secret (str): Twitter access secret
            project_dir (str): Project directory
            out_dir (str): Save directory for recorded tweets
            out_extension (str): File extension for recorded tweets, i.e. '.zip'
            task_file (str): Path to YAML file containing tasks to execute
            full_user_mentions (bool): For mentions, look up full user data
            appdata_token (str): Name to use for storing application data
            user_lookup_interval (int): Minutes between lookups of the same user
            appdata_timeout (float): Seconds to timeout for internal data store
            task_gen (List[Tuple[str, str]]): Task generators with keyword args
            remove_duplicates (bool): Ensures duplicated tweets/users are not
                                      recorded. Saves space, but can slow down
                                      the crawler.

        """
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_secret = access_secret

        self._project_dir = project_dir or DEFAULT_PROJECT_DIR
        self._appdata_token = appdata_token or APP_DATA_TOKEN
        self._out_dir = out_dir or os.path.join(self._project_dir, 'output')
        self._out_extension = out_extension or DEFAULT_OUTPUT_EXTENSION
        self._task_file = task_file or os.path.join(self._project_dir, 'tasks.yaml')

        self._full_user_mentions = full_user_mentions
        self._user_lookup_interval = user_lookup_interval
        self._appdata_timeout = appdata_timeout

        self._task_gen = self.parse_task_generators(task_gen)
        self._remove_duplicates = remove_duplicates

    @staticmethod
    def parse_task_generators(task_gen: Optional[List[Tuple[str, str]]]) -> List[Tuple[str, dict]]:
        """
        Convert incoming string kwargs to dict.

        Args:
            task_gen: Task generators

        Returns:
            Parsed task generators

        """
        generators = []
        for generator, kwarg_str in task_gen:
            if not kwarg_str:
                continue
            kwargs = {}
            for kwarg in kwarg_str.split(','):
                key, value = kwarg.split('=')
                kwargs[key] = value
            generators.append((generator, kwargs))
        return generators

    @property
    def consumer_key(self) -> str:
        """
        Twitter consumer key.
        """
        return self._consumer_key

    @property
    def consumer_secret(self) -> str:
        """
        Twitter consumer secret.
        """
        return self._consumer_secret

    @property
    def access_token(self) -> str:
        """
        Twitter access token.
        """
        return self._access_token

    @property
    def access_secret(self) -> str:
        """
        Twitter access secret.
        """
        return self._access_secret

    @property
    def project_dir(self) -> str:
        """
        Project directory.
        """
        return self._project_dir

    @property
    def out_dir(self) -> str:
        """
        Save directory for recorded tweets.
        """
        return self._out_dir

    @property
    def out_extension(self) -> str:
        """
        File extension for recorded tweets, i.e. '.zip'.
        """
        return self._out_extension

    @property
    def task_file(self) -> str:
        """
        Path to YAML file containing tasks to execute.
        """
        return self._task_file

    @property
    def full_user_mentions(self) -> bool:
        """
        For mentions, look up full user data.
        """
        return self._full_user_mentions

    @property
    def user_lookup_interval(self) -> int:
        """
        Minutes between lookups of the same user.
        """
        return self._user_lookup_interval

    @property
    def appdata_timeout(self) -> float:
        """
        Seconds to timeout for internal data store.
        """
        return self._appdata_timeout

    @property
    def task_gen(self) -> List[Tuple[str, dict]]:
        """
        Task generators.
        """
        return self._task_gen

    @property
    def remove_duplicates(self) -> bool:
        """
        Ensures duplicated tweets/users are not recorded. Saves space, but can
        slow down the crawler.

        Returns:
            True if duplicates should be removed, else False

        """
        return self._remove_duplicates

    @property
    def appdata_token(self) -> str:
        """
        Name to use for storing application data.
        """
        return self._appdata_token

    @property
    def appdata_dir(self) -> str:
        """
        Directory for storing internal data.
        """
        return os.path.join(self._project_dir, 'appdata')

    @property
    def appdata(self) -> str:
        """
        SQLite file for storing internal data.
        """
        return os.path.join(self.appdata_dir, f'{self.appdata_token}.sql')

    @property
    def log_dir(self) -> str:
        """
        Log directory.
        """
        return os.path.join(self._project_dir, 'logs')

    @property
    def logs(self) -> str:
        """
        Log file.
        """
        return os.path.join(self.log_dir, f'{self.appdata_token}.log')


def load(consumer_key=None, consumer_secret=None, access_token=None,
         access_secret=None, project_dir=None, out_dir=None, out_extension=None,
         task_file=None, full_user_mentions=False,
         appdata_token: str = APP_DATA_TOKEN,
         user_lookup_interval=DEFAULT_EXPAND_USERS_INTERVAL,
         appdata_timeout=DEFAULT_APP_DATA_CONNECTION_TIMEOUT,
         task_gen: Optional[List[Tuple[str, str]]] = None,
         remove_duplicates: bool = True):
    """
    Function to populate config and assign it to twicorder.config.Config.

    Args:
        consumer_key (str): Twitter consumer key
        consumer_secret (str): Twitter consumer secret
        access_token (str): Twitter access token
        access_secret (str): Twitter access secret
        project_dir (str): Project directory
        out_dir (str): Save directory for recorded tweets
        out_extension (str): File extension for recorded tweets, i.e. '.zip'
        task_file (str): Path to YAML file containing tasks to execute
        full_user_mentions (bool): For mentions, look up full user data
        appdata_token (str): Name to use for storing application data
        user_lookup_interval (int): Minutes between lookups of the same user
        appdata_timeout (float): Seconds to timeout for internal data store
        task_gen (List[Tuple[str, str]]): Task generators with keyword args
        remove_duplicates (bool): Ensures duplicated tweets/users are not
                                  recorded. Saves space, but can slow down the
                                  crawler.
    """
    global Config
    Config = _Config(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_secret=access_secret,
        project_dir=project_dir,
        out_extension=out_extension,
        out_dir=out_dir,
        task_file=task_file,
        full_user_mentions=full_user_mentions,
        appdata_token=appdata_token,
        user_lookup_interval=user_lookup_interval,
        appdata_timeout=appdata_timeout,
        task_gen=task_gen or [('config', '')],
        remove_duplicates=remove_duplicates,
    )
