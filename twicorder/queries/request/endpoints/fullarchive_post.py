#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.constants import RequestMethod
from twicorder.queries import TweetRequestQuery


class FullArchivePostQuery(TweetRequestQuery):

    name = 'fullarchive_post'
    endpoint = '/tweets/search/fullarchive/production'
    _next_cursor_path = 'next'
    _request_method = RequestMethod.Post
