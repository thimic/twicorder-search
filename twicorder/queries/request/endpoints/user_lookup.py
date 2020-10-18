#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import httpx

from twicorder.appdata import AppData
from twicorder.queries import ProductionRequestQuery


class UserLookupQuery(ProductionRequestQuery):
    """
    Example for tasks.yaml:

    user_lookups:                          # Endpoint name
      - frequency: 60                      # Interval between repeating queries in minutes
        iterations: 1                      # Number of times to repeat the query, 0 means indefinitely
        output: twitter/followers/users    # Output directory, relative to project directory
        kwargs:                            # Keyword Arguments to feed to endpoint
          user_id: 783214,6253282          # Comma separated list of user IDs, max 100
          include_entities: false          # Include entities node with statuses
      - frequency: 60                      # Interval between repeating queries in minutes
        iterations: 1                      # Number of times to repeat the query, 0 means indefinitely
        output: twitter/followers/users    # Output directory, relative to project directory
        kwargs:
          screen_name: twitterapi,twitter  # Comma separated list of screen names, max 100

    """

    name = 'user_lookups'
    endpoint = '/users/lookup'
    result_type = ProductionRequestQuery.ResultType.UserList

    def __init__(self, app_data: AppData, output: str = None,
                 max_count: int = 0, **kwargs):
        super().__init__(app_data, output, max_count, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    async def finalise(self, response: httpx.Response):
        """
        Method called immediately after the query runs.

        Args:
            response: Response to query

        """
        await super().finalise(response)
        await self.bake_ids()
        self.log(f'Cached {self.type.name} IDs to disk!')
