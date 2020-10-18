#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.queries import BaseRequestQuery


class RateLimitStatusQuery(BaseRequestQuery):

    name = 'rate_limit_status'
    endpoint = '/application/rate_limit_status'
    result_type = BaseRequestQuery.ResultType.RateLimit
