#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import time

from twicorder.queries.request.base import BaseRequestQuery
from twicorder.rate_limits import RateLimitCentral


class ProductionRequestQuery(BaseRequestQuery):
    """
    Base class for production queries. These are queries that should have their
    rate limits counted.
    """

    async def setup(self):
        """
        Method called immediately before the query runs.
        """
        await super().setup()
        # Check rate limit for query. Sleep if limits are in effect.
        limits = {}

        # Loop over available auth methods to check for rate limits
        for auth_method in self.auth_methods:
            limit = await RateLimitCentral.get(
                app_data=self.app_data,
                auth_method=auth_method,
                endpoint=self.endpoint
            )
            self.log(f'{auth_method.name}: {limit}')

            # If rate limit is in effect for this method, log it and try the
            # next one
            if limit and limit.remaining == 0:
                limits[auth_method] = limit
            else:
                self._auth_method = auth_method
                break

        # If all methods were logged, rate limits are in effect everywhere.
        # Pick the auth method with the closest reset and wait.
        if self.auth_methods and len(limits) == len(self.auth_methods):
            shortest_wait = sorted(limits.items(), key=lambda x: x[1].reset)[0]
            self._auth_method = shortest_wait[0]
            sleep_time = max(shortest_wait[1].reset - time.time(), 0) + 2
            msg = (
                f'Sleeping for {sleep_time:.02f} seconds for endpoint '
                f'"{self.endpoint}".'
            )
            self.log(msg)
            await asyncio.sleep(sleep_time)

    async def finalise(self, response: httpx.Response):
        """
        Method called immediately after the query runs.

        Args:
            response: Response to query

        """
        await super().finalise(response)

        # Update rate limit for query
        RateLimitCentral.update(
            auth_method=self.auth_method,
            endpoint=self.endpoint,
            header=response.headers
        )

        # Save and store IDs for crawled tweets found in the query result.
        # Also record the last tweet ID found.
        if self.results:
            # Todo: Save in callback! Don't bake IDs before successful save?
            # await self.save()
            pass
