#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests

from requests.auth import AuthBase
from requests_oauthlib import OAuth1Session

from twicorder import NoCredentialsException
from twicorder.config import Config


class Auth:
    """
    Class for handling API authentication.
    """
    _session = None
    _bearer_token = None

    @classmethod
    def session(cls):
        """
        Creates an OAuth1Session or returns an existing one.

        Returns:
            OAuth1Session: Logged in session

        """
        if not (Config.consumer_key and Config.consumer_secret):
            raise NoCredentialsException
        if not cls._session:
            cls._session = OAuth1Session(
                client_key=Config.consumer_key,
                client_secret=Config.consumer_secret
            )
        return cls._session

    @classmethod
    def token(cls):
        """
        Requests an OAuth2 bearer token from the API.

        Returns:
            OAuth2Bearer: Token object

        """
        if not (Config.consumer_key and Config.consumer_secret):
            raise NoCredentialsException
        if not cls._bearer_token:
            resp = requests.post(
                'https://api.twitter.com/oauth2/token',
                auth=(Config.consumer_key, Config.consumer_secret),
                data={'grant_type': 'client_credentials'}
            )
            data = resp.json()
            token_type = data.get('token_type')
            if token_type != 'bearer':
                msg = (
                    f'Expected token_type to equal "bearer", but got '
                    f'{token_type} instead.'
                )
                raise AttributeError(msg)

            cls._bearer_token = OAuth2Bearer(data['access_token'])
        return cls._bearer_token


class OAuth2Bearer(AuthBase):
    """
    Bearer token implementation for requests.auth.
    """
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.bearer_token
        return request
