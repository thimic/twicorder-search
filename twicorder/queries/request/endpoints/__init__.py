#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import inspect
import os

from twicorder.queries.request.base import BaseRequestQuery


# Import all query classes in the package deriving from BaseRequestQuery
this_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
for filename in os.listdir(this_dir):
    if not filename.endswith('.py'):
        continue
    module_name = os.path.splitext(filename)[0]
    module = importlib.import_module(f'.{module_name}', __package__)
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if cls == BaseRequestQuery:
            continue
        elif issubclass(cls, BaseRequestQuery):
            globals()[name] = cls
