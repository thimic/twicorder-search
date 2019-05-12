#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from threading import Lock

from twicorder.utils import collect_key_values
from twicorder.config import Config
from twicorder.constants import DEFAULT_EXPAND_USERS_INTERVAL
from twicorder.queries import RequestQuery


class UserQuery(RequestQuery):

    name = 'user'
    endpoint = '/users/lookup'

    def __init__(self, output=None, **kwargs):
        super(UserQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    def bake_ids(self):
        return

    def save(self):
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
    _config = Config.get()
    _cache_life = timedelta(
        minutes=_config.get(
            'user_lookup_interval',
            DEFAULT_EXPAND_USERS_INTERVAL
        )
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
    def expand_user_mentions(cls, tweets):
        """
        Expands user mentions for tweets in result. Performs API user lookup if
        no data is found for the given mention.

        Args:
            tweets (list[dict]): List of tweets

        Returns:
            list[dict]: List of tweets with expanded user mentions

        """
        with cls.lock:
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
                UserQuery(user_id=','.join([str(u) for u in chunk])).run()
            for tweet in tweets:
                mention_sections = collect_key_values('user_mentions', tweet)
                for mention_section in mention_sections:
                    for mention in mention_section:
                        full_user = cls.users.get(mention['id'])
                        if not full_user:
                            continue
                        mention.update(full_user.data)
        return tweets
