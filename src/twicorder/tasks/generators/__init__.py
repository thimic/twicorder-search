#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import importlib.util
import inspect
import os
import sys

from pathlib import Path
from typing import Dict, Type

from twicorder.tasks.generators.base_generator import BaseTaskGenerator


def load_generators() -> Dict[str, Type[BaseTaskGenerator]]:
    """
    Dictionary of task generators by name
    """
    task_generators = {}
    paths = []

    # Included task generators
    this_dir = Path(inspect.getfile(inspect.currentframe())).parent
    paths.append(this_dir)

    # Third party task generators
    plugin_dir = os.getenv('TWICORDER_TASKGEN_PATH')
    if plugin_dir:
        paths.append(Path(plugin_dir))

    # Perform import
    for path in paths:
        if not path.exists():
            continue
        for filename in Path(path).iterdir():
            if not filename.stem.endswith('_generator'):
                continue
            module_name = filename.stem

            spec = importlib.util.spec_from_file_location(module_name, str(filename))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if cls == BaseTaskGenerator:
                    continue
                elif issubclass(cls, BaseTaskGenerator):
                    task_generators[cls.name] = cls

    return task_generators
