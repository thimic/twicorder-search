#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.queries import ProductionRequestQuery


class FriendsList(ProductionRequestQuery):

    name = 'friends_list'
    endpoint = '/friends/list'
    result_type = ProductionRequestQuery.ResultType.UserList
