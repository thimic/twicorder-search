#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests

from requests.auth import AuthBase
from requests_oauthlib import OAuth1Session


class Auth:
    """
    Class for accessing the Auth handler
    """
    session = OAuth1Session(
        os.getenv('CONSUMER_KEY'),
        client_secret=os.getenv('CONSUMER_SECRET')
    )

    def __new__(cls, *args, **kwargs):
        return cls.session


class TokenAuth:
    """
    Class for accessing the Bearer Token
    """

    _bearer_token = ''

    def __init__(self):
        resp = requests.post(
            'https://api.twitter.com/oauth2/token',
            auth=(os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET')),
            data={'grant_type': 'client_credentials'}
        )
        data = resp.json()
        token_type = data.get('token_type')
        if token_type != 'bearer':
            msg = (
                f'Expected token_type to equal "bearer", but got {token_type} '
                f'instead.'
            )
            raise AttributeError(msg)

        self._bearer_token = data['access_token']

    @property
    def bearer(self):
        return OAuth2Bearer(self._bearer_token)


class OAuth2Bearer(AuthBase):
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.bearer_token
        return request
