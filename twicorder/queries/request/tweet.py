#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import httpx

from datetime import datetime

from twicorder.config import Config
from twicorder.constants import DEFAULT_EXPAND_USERS, TW_TIME_FORMAT
from twicorder.queries.request.production import ProductionRequestQuery


class TweetRequestQuery(ProductionRequestQuery):
    """
    Base class for queries returning tweets.
    """

    _mongo_support = True

    def result_timestamp(self, result):
        """
        For a given result produced by the current query, return its time stamp.

        Args:
            result (dict): One single result object

        Returns:
            datetime.datetime): Timestamp

        """
        created_at = result['created_at']
        return datetime.strptime(created_at, TW_TIME_FORMAT)

    def result_id(self, result: dict) -> str:
        """
        For a given result produced by the current query, return its ID.

        Args:
            result (dict): One single result object

        Returns:
            str: Result ID

        """
        return str(result['id'])

    async def finalise(self, response: httpx.Response):
        """
        Method called immediately after the query runs.

        Args:
            response: Response to query

        """
        await super().finalise(response)
        await self.bake_ids()
        self.log(f'Cached {self.type.name} IDs to disk!')
        if self.results:
            self.last_cursor = self.results[0].get('id')

        # Cache last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self.last_cursor:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            await self.app_data.set_last_cursor(self.uid, self.last_cursor)

    async def save(self):
        """
        Save the results of the query to disk.
        """
        if self._results and self._output:
            from twicorder.cached_users import CachedUserCentral
            if Config.full_user_mentions or DEFAULT_EXPAND_USERS:
                self.log('Expanding user mentions!')
                await CachedUserCentral.expand_user_mentions(
                    self.app_data,
                    self.results
                )
        await super().save()
