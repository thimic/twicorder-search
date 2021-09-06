#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http import HTTPStatus


class TwicorderException(BaseException):
    pass


class NoTasksException(TwicorderException):

    def __init__(self, *args, **kwargs):
        if not args:
            from twicorder.config import Config
            args = [(
                f'\n'
                f'A tasks.yaml file could not be found for this project '
                f'directory ({Config.project_dir}). Please create one.\n'
                f'\n'
                f'To set a different project directory, please run Twicorder '
                f'with the "--project-dir" option:\n'
                f'\n'
                f'  twicorder --project-dir /path/to/project_dir\n'
                f'\n'
                f'To specify a custom path to the task file, please run Twicorder '
                f'with the "--task-file" option:\n'
                f'\n'
                f'  twicorder --task-file /path/to/tasks.yaml\n'
                f'\n'
                f'See '
                f'https://github.com/thimic/twicorder-search/blob/master/'
                f'README.md for details.'
            )]
        super().__init__(*args, **kwargs)


class NoCredentialsException(TwicorderException):

    def __init__(self, *args, **kwargs):
        if not args:
            args = [(
                '\n'
                'No API credentials found. Credentials can be added as launch '
                'arguments or set as environment variables:\n'
                '\n'
                ' - TWICORDER_CONSUMER_KEY\n'
                ' - TWICORDER_CONSUMER_SECRET\n'
                ' - TWICORDER_ACCESS_TOKEN\n'
                ' - TWICORDER_ACCESS_SECRET\n'
                '\n'
                'See https://github.com/thimic/twicorder-search/blob/master/'
                'README.md for details.'
            )]
        super().__init__(*args, **kwargs)


class UnauthorisedException(TwicorderException):

    code = HTTPStatus.UNAUTHORIZED


class ForbiddenException(TwicorderException):

    code = HTTPStatus.FORBIDDEN


class RatelimitException(TwicorderException):

    code = HTTPStatus.TOO_MANY_REQUESTS
