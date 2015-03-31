# -*- coding: utf-8 -*-
'''
Project manager. Part of brainy daemon.


@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT). Read a copy of LICENSE distributed with
          this code.

Copyright (c) 2014-2015 Pelkmans Lab
'''
import os
import logging
from brainy.utils import load_yaml, dump_yaml
# Import everything from a command line interface.
from sh import brainy as brainy_shell

logger = logging.getLogger(__name__)


class FatalProjectError(object):
    '''Stop any further progress'''


class ProjectManager(object):

    def __init__(self, project_list_path, create_missing_project_folders=True):
        self.project_list_path = project_list_path
        self.create_missing_project_folders = create_missing_project_folders
        self._projects = []
        self.load_projects()

    @property
    def projects(self):
        '''
        An iterator that takes care of a lot of logical consistency checks.
        '''
        for project in self._projects:
            # Project is a dictionary with all keys being optional except for
            # path.
            if 'path' not in project:
                raise KeyError('Path to a project is to specified.')
            if 'name' not in project:
                # Assume from the path of the project.
                project['name'] == os.path.basename(project['path'])
            # Assert project path ends with the project name.
            if not project['path'].endswith(project['name']):
                logger.warn('Project path does not end with the project name.')
                project['path'] = os.path.join(project['path'],
                                               project['name'])
            # Assert project path exists.
            if not os.path.exists(project['path']):
                logger.warn('Project is registered but not folder exists yet.')
                if not self.create_missing_project_folders:
                    raise IOError('Project path does not exists: %s' %
                                  project['path'])
                logger.info('Creating a missing registered project path: %s' %
                            project['path'])
                os.makedirs(project['path'])
            # Resolve more properties.
            project['config_path'] = os.path.join(project['path'], '.brainy')
            project['is_initialized'] = os.path.exists(project['config_path'])
            # Yield valid dictionary.
            yield project

    def load_projects(self):
        '''
        Load/init a YAML file listing brainy projects. The expected content of
        the YAML file is:

        registered_projects:
          -
            path: "/tmp/demo"
            name: "demo"

        '''
        if os.path.exists(self.project_list_path):
            # There is a non-empty list of registered projects.
            project_structure = load_yaml(open(self.project_list_path).read())
            self._projects = project_structure['registered_projects']
        else:
            # Project list is empty. Simply initialize it.
            self._projects = []
            with open(self.project_list_path, 'w+') as stream:
                stream.write(dump_yaml(self._projects))

    def log_shell_output(self, output, level=logging.INFO):
        # Logging goes into stderr
        logger.log(level, '--LOG--')
        logger.log(level, output.stderr)
        logger.log(level, '--STDOUT--')
        logger.log(level, output.stdout)

    def build_projects(self):
        logger.info('Initialize empty brainy projects '
                    'with a default workflow.')
        try:
            for project in self.projects:
                # Was project initialized?
                if not project['is_initialized']:
                    logger.info('Initializing {%s}' % project['name'])
                    output = brainy_shell.project('create',
                                                  '-p', project['path'],
                                                  project['name'])
                    if output.exit_code != 0:
                        self.log_shell_output(output, level=logging.ERROR)
                        logger.error('Failed to initialize project: %s' %
                                     project['name'])
                        continue
                    # All fine.
                    self.log_shell_output(output)

        except Exception as error:
            logger.exception(error)

    def run_projects(self):
        logger.info('Run brainy projects')
        try:
            for project in self.projects:
                # Was project initialized?
                if project['is_initialized']:
                    logger.info('Running {%s}' % project['name'])
                    output = brainy_shell.project('run',
                                                  '-p', project['path'])
                    if output.exit_code != 0:
                        self.log_shell_output(output, level=logging.ERROR)
                        logger.error('Failed to run project: %s' %
                                     project['name'])
                        continue
                    # All fine.
                    self.log_shell_output(output)
        except Exception as error:
            logger.exception(error)

