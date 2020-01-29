#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests

from requests.auth import AuthBase

from oauth2 import Client, Consumer, Token

from twicorder import NoCredentialsException
from twicorder.config import Config
from twicorder.constants import AuthMethod, RequestMethod


class Response:

    def __init__(self, status, reason, headers, data):
        self._status = status
        self._reason = reason
        self._headers = headers
        if isinstance(data, (str, bytes, bytearray)):
            self._data = json.loads(data)
        else:
            self._data = data

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    @property
    def headers(self):
        return self._headers

    @property
    def data(self):
        return self._data


class AuthHandler:
    """
    Class for handling API authentication.
    """
    _session = None
    _bearer_token = None
    _client = None

    @classmethod
    def client(cls):
        """
        Creates an oauth2.Client objects or returns an existing one.

        Returns:
            oauth2.Client: Logged in client

        """
        if not (Config.consumer_key and Config.consumer_secret):
            raise NoCredentialsException
        if not (Config.access_token and Config.access_secret):
            raise NoCredentialsException

        if not cls._client:
            consumer = Consumer(
                key=Config.consumer_key,
                secret=Config.consumer_secret
            )
            access_token = Token(
                key=Config.access_token,
                secret=Config.access_secret
            )
            cls._client = Client(consumer, access_token)
        return cls._client

    @classmethod
    def token(cls):
        """
        Requests an OAuth2 bearer token from the API.

        Returns:
            OAuth2Bearer: Token bearer object

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

    @classmethod
    def request(cls, auth_method: AuthMethod, uri: str, method: RequestMethod,
                headers=None):
        if auth_method is AuthMethod.App:
            return cls.app_request(uri=uri, method=method, headers=headers)
        elif auth_method is AuthMethod.User:
            return cls.user_request(uri=uri, method=method, headers=headers)

    @classmethod
    def user_request(cls, uri: str, method: RequestMethod,
                     headers=None) -> Response:
        if headers is None:
            headers = {}
        client = cls.client()
        resp, data = client.request(
            uri,
            method=method.value.upper(),
            headers=headers
        )
        resp_headers = {k: v for k, v in resp.items()}
        response = Response(
            status=resp.status,
            reason=resp.reason,
            headers=resp_headers,
            data=data
        )
        return response

    @classmethod
    def app_request(cls, uri: str, method: RequestMethod,
                    headers=None) -> Response:
        if headers is None:
            headers = {}
        resp = requests.request(
            method=method.value,
            url=uri,
            headers=headers,
            auth=cls.token()
        )
        response = Response(
            status=resp.status_code,
            reason=resp.reason,
            headers=resp.headers,
            data=resp.json()
        )
        return response


class OAuth2Bearer(AuthBase):
    """
    Bearer token implementation for requests.auth.
    """
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.bearer_token
        return request
