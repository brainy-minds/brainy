'''
brainy.project

Manage projects.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2014 Pelkmans Lab
'''

import os
import logging
logger = logging.getLogger(__name__)
from brainy.version import brainy_version
from brainy.utils import merge_dicts
from brainy.config import (write_project_config, load_project_config,
                           load_user_config, project_has_config)
from brainy.workflows import bootstrap_workflow
from brainy.scheduler import BrainyScheduler
from brainy.pipes import PipesManager


class BrainyProjectError(Exception):
    '''Thrown by brainy project if the logic goes wrong.'''


class BrainyProject(object):

    def __init__(self, name, path):
        self.name = name
        if os.path.basename(path) != name:
            # Append name to full path of the project folder if it is not
            # ending with such.
            self.path = os.path.join(path, name)
        else:
            self.path = path
        self.config = None
        self.scheduler = None

    def create(self, from_workflow='canonical', inherit_config={},
               override_config={}):
        # Make project dir.
        if not os.path.exists(self.path):
            logger.info('Creating new project folder: %s' % self.path)
            os.mkdir(self.path)
        else:
            raise BrainyProjectError('Project folder already exists: %s' %
                                     self.path)
        # Put basic YAML config during project creation. This is required for
        # project to be valid. We will also check version compatibility.
        write_project_config(self.path, inherit_config=inherit_config,
                             override_config=override_config)

        # Bootstrap project with a standard iBRAIN workflow.
        bootstrap_workflow(self.path, workflow_name=from_workflow)

    def is_a_valid_project_folder(self):
        return project_has_config(self.path)

    def load_config(self):
        self.config = load_user_config()
        project_config = load_project_config(self.path)
        logger.info('Overwriting global configuration with project specific.')
        self.config = merge_dicts(self.config, project_config)

    def run(self, manager_cls=PipesManager):
        '''
        Load project configuration. Discover and process pipelines using the
        specified scheduler.
        '''
        logger.info('Loading configuration')
        self.load_config()
        logger.info('Initializing "%s" as a scheduling engine' %
                    self.config['scheduling']['engine'])
        self.scheduler = BrainyScheduler.build_scheduler(
            self.config['scheduling']['engine'])
        self.pipes = manager_cls(self)
        logger.info('Starting pipelines discovery and processing..')
        self.pipes.process_pipelines()
        logger.info('Finished pipelines processing.')

