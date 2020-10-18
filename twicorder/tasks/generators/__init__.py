#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import inspect
import os

from typing import Dict, Type

from .base_generator import BaseTaskGenerator


def load_generators() -> Dict[str, Type[BaseTaskGenerator]]:
    """
    Dictionary of task generators by name
    """
    task_generators = {}
    this_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
    for filename in os.listdir(this_dir):
        if not filename.endswith('.py'):
            continue
        module_name = os.path.splitext(filename)[0]
        module = importlib.import_module(f'.{module_name}', __package__)
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls == BaseTaskGenerator:
                continue
            elif issubclass(cls, BaseTaskGenerator):
                task_generators[cls.name] = cls
    return task_generators
