#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import yaml

from unittest import TestCase

from twicorder import NoTasksException
from twicorder.tasks.manager import TaskManager
from twicorder.tasks.task import Task


class TestTask(TestCase):

    def setUp(self) -> None:
        self.oneoff_task = Task(
            name='user_timeline',
            taskgen='test',
            frequency=1,
            iterations=1,
            output='foo/timeline',
            screen_name='foo'
        )

        self.repeating_task = Task(
            name='user_timeline',
            taskgen='test',
            frequency=15,
            iterations=0,
            output='bar/timeline',
            screen_name='bar'
        )

    def tearDown(self) -> None:
        self.oneoff_task = None
        self.repeating_task = None

    def test__repr__(self):
        oneoff_expectation = (
            'Task('
            'name=\'user_timeline\', '
            'taskgen=\'test\', '
            'frequency=1, '
            'iterations=1, '
            'output=\'foo/timeline\', '
            'kwargs={\'screen_name\': \'foo\'}'
            ')'
        )
        self.assertEqual(oneoff_expectation, repr(self.oneoff_task))

        repeating_expectation = (
            'Task('
            'name=\'user_timeline\', '
            'taskgen=\'test\', '
            'frequency=15, '
            'iterations=0, '
            'output=\'bar/timeline\', '
            'kwargs={\'screen_name\': \'bar\'}'
            ')'
        )
        self.assertEqual(repeating_expectation, repr(self.repeating_task))

    def test_name(self):
        self.assertEqual('user_timeline', self.oneoff_task.name)
        self.assertEqual('user_timeline', self.repeating_task.name)

    def test_frequency(self):
        self.assertEqual(1, self.oneoff_task.frequency)
        self.assertEqual(15, self.repeating_task.frequency)

    def test_iterations(self):
        self.assertEqual(1, self.oneoff_task.iterations)
        self.assertEqual(0, self.repeating_task.iterations)

    def test_output(self):
        self.assertEqual('foo/timeline', self.oneoff_task.output)
        self.assertEqual('bar/timeline', self.repeating_task.output)

    def test_kwargs(self):
        self.assertDictEqual({'screen_name': 'foo'}, self.oneoff_task.kwargs)
        self.assertDictEqual({'screen_name': 'bar'}, self.repeating_task.kwargs)


class TestTaskManager(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.project_dir = tempfile.mkdtemp()

    @classmethod
    def setUpConfig(cls):
        raw_tasks = {
            'user_timeline': [
                {
                    'frequency': 1,
                    'iterations': 1,
                    'output': 'oneoff/timeline',
                    'kwargs': {'screen_name': 'oneoff'}
                },
                {
                    'frequency': 5,
                    'iterations': 10,
                    'output': 'finite/timeline',
                    'kwargs': {'screen_name': 'finite'}
                },
                {
                    'frequency': 15,
                    'iterations': 0,
                    'output': 'repeating/timeline',
                    'kwargs': {'screen_name': 'repeating'}
                },
            ],
        }

        tasks_file = os.path.join(cls.project_dir, 'tasks.yaml')
        with open(tasks_file, 'w') as stream:
            yaml.safe_dump(raw_tasks, stream)

        from twicorder import config
        config.load(project_dir=cls.project_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.project_dir)

    def test_missing_tasks(self):
        from twicorder import config
        config.load(project_dir=tempfile.mkdtemp())
        self.assertRaises(NoTasksException, TaskManager, [('config', {})])

    def test_tasks(self):
        self.setUpConfig()
        manager = TaskManager([('config', {})])
        self.assertEqual(3, len(manager.tasks))

        # Oneoff
        self.assertEqual(1, manager.tasks[0].frequency)
        self.assertEqual(1, manager.tasks[0].iterations)
        self.assertEqual(1, manager.tasks[0].remaining)
        self.assertEqual('oneoff/timeline', manager.tasks[0].output)
        self.assertDictEqual(
            {'max_count': 0, 'screen_name': 'oneoff'},
            manager.tasks[0].kwargs
        )
        self.assertFalse(manager.tasks[0].done)

        # Finite
        self.assertEqual(5, manager.tasks[1].frequency)
        self.assertEqual(10, manager.tasks[1].iterations)
        self.assertEqual(10, manager.tasks[1].remaining)
        self.assertEqual('finite/timeline', manager.tasks[1].output)
        self.assertDictEqual(
            {'max_count': 0, 'screen_name': 'finite'},
            manager.tasks[1].kwargs
        )
        self.assertFalse(manager.tasks[1].done)

        # Repeating
        self.assertEqual(15, manager.tasks[2].frequency)
        self.assertEqual(0, manager.tasks[2].iterations)
        self.assertEqual(0, manager.tasks[2].remaining)
        self.assertEqual('repeating/timeline', manager.tasks[2].output)
        self.assertDictEqual(
            {'max_count': 0, 'screen_name': 'repeating'},
            manager.tasks[2].kwargs
        )
        self.assertFalse(manager.tasks[2].done)
