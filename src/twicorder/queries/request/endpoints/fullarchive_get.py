#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.queries import TweetRequestQuery


class FullArchiveGetQuery(TweetRequestQuery):

    name = 'fullarchive_get'
    endpoint = '/tweets/search/fullarchive/production'
    _next_cursor_path = 'next'
