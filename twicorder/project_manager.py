#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from twicorder.constants import APP_DATA_TOKEN, DEFAULT_PROJECT_DIR


class _ProjectManager:
    """
    Class for handling file paths related to the current project.
    """
    _project_dir = DEFAULT_PROJECT_DIR

    @property
    def project_dir(self):
        project_path = self._project_dir
        os.makedirs(project_path, exist_ok=True)
        return project_path

    @project_dir.setter
    def project_dir(self, value):
        self._project_dir = os.path.expanduser(value)

    @property
    def config_dir(self):
        config_path = os.path.join(self.project_dir, 'config')
        os.makedirs(config_path, exist_ok=True)
        return config_path

    @property
    def output_dir(self):
        output_path = os.path.join(self.project_dir, 'tweets')
        os.makedirs(output_path, exist_ok=True)
        return output_path

    @property
    def app_data_dir(self):
        app_data_path = os.path.join(self.project_dir, 'app_data')
        os.makedirs(app_data_path, exist_ok=True)
        return app_data_path

    @property
    def logs_dir(self):
        log_path = os.path.join(self.app_data_dir, 'logs')
        os.makedirs(log_path, exist_ok=True)
        return log_path

    @property
    def preferences(self):
        return os.path.join(self.config_dir, 'preferences.yaml')

    @property
    def tasks(self):
        return os.path.join(self.config_dir, 'tasks.yaml')
    
    @property
    def logs(self):
        return os.path.join(self.logs_dir, f'{APP_DATA_TOKEN}.log')

    @property
    def app_data(self):
        return os.path.join(self.app_data_dir, f'{APP_DATA_TOKEN}.sql')


ProjectManager = _ProjectManager()
