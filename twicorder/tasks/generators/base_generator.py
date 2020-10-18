#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import List

from twicorder.tasks.task import Task


class BaseTaskGenerator(ABC):
    """
    Base task generator. Generates a set of TwiCorder tasks on fetch().
    """

    name = NotImplemented

    def __init__(self, *args, **kwargs):
        """
        Entry point for BaseTaskGenerator.
        """
        self._tasks = []

    @property
    def tasks(self) -> List[Task]:
        """
        List of generated tasks.
        """
        return self._tasks

    def clear(self):
        """
        Clear all tasks.
        """
        self._tasks = []

    @abstractmethod
    def fetch(self):
        """
        Method to generate tasks. Should populate BaseTaskGenerator._tasks.
        """
        ...
