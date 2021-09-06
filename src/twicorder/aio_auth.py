#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx

from typing import Optional

from authlib.integrations.httpx_client import (
    AsyncOAuth1Client,
    AsyncOAuth2Client,
)
from twicorder.config import Config
from twicorder.constants import (
    AuthMethod,
    RequestMethod,
    TOKEN_ENDPOINT,
)


class AsyncAuthHandler:

    _app_client: Optional[AsyncOAuth2Client] = None
    _user_client: Optional[AsyncOAuth1Client] = None

    @classmethod
    async def app_client(cls) -> AsyncOAuth2Client:
        """
        Create App Client or return existing one.

        Returns:
            App Client

        """
        if not cls._app_client:
            app_client = AsyncOAuth2Client(
                client_id=Config.consumer_key,
                client_secret=Config.consumer_secret
            )
            await app_client.fetch_token(
                url=TOKEN_ENDPOINT,
                grant_type='client_credentials'
            )
            cls._app_client = app_client
        return cls._app_client

    @classmethod
    def user_client(cls) -> AsyncOAuth1Client:
        """
        Create User Client or return existing one.

        Returns:
            User Client

        """
        if not cls._user_client:
            cls._user_client = AsyncOAuth1Client(
                client_id=Config.consumer_key,
                client_secret=Config.consumer_secret,
                token=Config.access_token,
                token_secret=Config.access_secret
            )
        return cls._user_client

    @classmethod
    async def request(cls, auth_method: AuthMethod, method: RequestMethod,
                      url: str, params: dict = None, headers: dict = None
                      ) -> Optional[httpx._models.Response]:
        """
        Perform request for the given authentication and request method. Extract
        params from URL and pass it to the client as a dict.

        Args:
            auth_method: Authentiation method - App or User
            method: Request method - GET, POST etc
            url: Endpoint URL
            params: URL parameters
            headers: Request headers

        Returns:
            Request response

        """
        if auth_method is AuthMethod.App:
            client = await cls.app_client()
        elif auth_method is AuthMethod.User:
            client = cls.user_client()
        else:
            return
        while not client:
            await asyncio.sleep(.1)

        response = await client.request(
            method=method.value,
            url=url,
            params=params,
            headers=headers
        )
        return response


async def main():

    resp = await AsyncAuthHandler.request(
        auth_method=AuthMethod.User,
        method=RequestMethod.Get,
        url='https://api.twitter.com/1.1/search/tweets.json',
        params={'q': '%23bigsur', 'result_type': 'recent'}
    )

    print(resp.json())
    print(resp.headers['x-rate-limit-remaining'])
    print(type(resp))


if __name__ == '__main__':
    asyncio.run(main())
