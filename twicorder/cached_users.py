#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timedelta
from asyncio import Lock
from typing import Callable, Iterable, Optional

from twicorder.appdata import AppData
from twicorder.config import Config
from twicorder.constants import DEFAULT_EXPAND_USERS_INTERVAL
from twicorder.queries import ProductionRequestQuery
from twicorder.utils import collect_key_values


class UserQuery(ProductionRequestQuery):

    name = 'cached_user'
    endpoint = '/users/lookup'

    def __init__(self, app_data: AppData, taskgen: str, output: str = None,
                 max_count: int = 0,
                 stop_func: Optional[Callable[[UserQuery], bool]] = None,
                 **kwargs):
        super(UserQuery, self).__init__(app_data, taskgen, output, max_count, stop_func, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    async def save(self):
        for user in self.results:
            CachedUserCentral.add(user)


class CachedUser:
    """
    Class storing information about one cached user.
    """
    def __init__(self, user_data):
        """
        CachedUser constructor. Takes raw user data and records time of
        creation.

        Args:
            user_data (dict): Raw user data

        """

        self._data = user_data
        self._timestamp = datetime.now()

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    def __repr__(self):
        rep = (
            f'CachedUser('
            f'name={self.screen_name}, '
            f'timestamp={self.timestamp:%c}'
            f')'
        )
        return rep

    @property
    def uid(self):
        """
        User ID.

        Returns:
            int: Unique user ID

        """
        return self._data['id']

    @property
    def screen_name(self):
        """
        User screen name.

        Returns:
            str: User screen name

        """
        return self._data['screen_name']

    @property
    def data(self):
        """
        Raw data for user.

        Returns:
            dict: Raw user data

        """
        return self._data

    @property
    def timestamp(self):
        """
        User capture time.

        Returns:
            datetime.datetime: Time stamp for user capture

        """
        return self._timestamp


class CachedUserCentral:
    """
    A class to cache user lookups for a certain amount of time. This saves
    performing the same user lookup too frequently, which can lead to hitting
    rate limit caps.
    """

    users = {}
    _cache_life = timedelta(
        minutes=Config.user_lookup_interval or DEFAULT_EXPAND_USERS_INTERVAL
    )
    lock = Lock()

    @classmethod
    def add(cls, user):
        """
        Adds the given user to the cache.

        Args:
            user (dict): Raw user data

        """
        cls.users[user['id']] = CachedUser(user)

    @classmethod
    def filter(cls):
        """
        Filters out expired users from cache.
        """
        cls.users = {
            k: v for k, v in cls.users.items()
            if datetime.now() - v.timestamp <= cls._cache_life
        }

    @classmethod
    async def expand_user_mentions(cls, app_data: AppData, tweets: Iterable):
        """
        Expands user mentions for tweets in result. Performs API user lookup if
        no data is found for the given mention.

        Args:
            app_data: AppData object for persistent storage between sessions
            tweets (list[dict]): List of tweets

        Returns:
            list[dict]: List of tweets with expanded user mentions

        """
        # with cls.lock:
        cls.filter()
        missing_users = set([])
        for tweet in tweets:
            for user in collect_key_values('user', tweet):
                cls.add(user)
            mention_sections = collect_key_values('user_mentions', tweet)
            for mention_section in mention_sections:
                for mention in mention_section:
                    if not mention['id'] in cls.users:
                        missing_users.add(mention['id'])
        if not missing_users:
            return
        missing_users = list(missing_users)
        n = 100
        chunks = [
            missing_users[i:i + n] for i in range(0, len(missing_users), n)
        ]
        for chunk in chunks:
            await UserQuery(
                app_data,
                'twicorder',
                user_id=','.join([str(u) for u in chunk])
            ).start()

        for tweet in tweets:
            mention_sections = collect_key_values('user_mentions', tweet)
            for mention_section in mention_sections:
                for mention in mention_section:
                    full_user = cls.users.get(mention['id'])
                    if not full_user:
                        continue
                    mention.update(full_user.data)
        return tweets
