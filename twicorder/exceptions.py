#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class TwicorderException(BaseException):
    pass


class NoConfigException(TwicorderException):

    def __init__(self, *args, **kwargs):
        if not args:
            from twicorder.project_manager import ProjectManager
            args = [(
                f'\n'
                f'No configuration file could be found for this project '
                f'({ProjectManager.project_dir}). Configs are installed to '
                f'<PROJECT_ROOT>/config/preferences.yaml.\n'
                f'\n'
                f'To set a different project directory, please run Twicorder '
                f'with the "--project-dir" option:\n'
                f'\n'
                f'twicorder --project-dir /path/to/project_dir\n'
                f'\n'
                f'See '
                f'https://github.com/thimic/twicorder-search/blob/master/'
                f'README.md for details.'
            )]
        super().__init__(*args, **kwargs)


class NoTasksException(TwicorderException):

    def __init__(self, *args, **kwargs):
        if not args:
            from twicorder.project_manager import ProjectManager
            args = [(
                f'\n'
                f'No tasks file could be found for this project '
                f'({ProjectManager.project_dir}). Tasks are installed to '
                f'<PROJECT_ROOT>/config/tasks.yaml.\n'
                f'\n'
                f'To set a different project directory, please run Twicorder '
                f'with the "--project-dir" option:\n'
                f'\n'
                f'twicorder --project-dir /path/to/project_dir\n'
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
                'No API credentials found. Credentials can be added to the '
                'project config or set as environment variables:\n'
                '\n'
                ' - TWITTER_CONSUMER_KEY\n'
                ' - TWITTER_CONSUMER_SECRET\n'
                ' - TWITTER_ACCESS_TOKEN\n'
                ' - TWITTER_ACCESS_SECRET\n'
                '\n'
                'See https://github.com/thimic/twicorder-search/blob/master/'
                'README.md for details.'
            )]
        super().__init__(*args, **kwargs)
