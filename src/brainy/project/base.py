'''
brainy.project

Manage projects.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2014 Pelkmans Lab
'''

import os
import shutil
import logging
from brainy.version import brainy_version
from brainy.utils import merge_dicts
from brainy.config import (write_project_config, load_project_config,
                           load_user_config, project_has_config)
from brainy.workflows import bootstrap_workflow
from brainy.scheduler import BrainyScheduler
from brainy.pipes.manager import PipesManager
from brainy.errors import BrainyProjectError
from brainy.project.report import report_data
logger = logging.getLogger(__name__)


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

    @property
    def report_folder_path(self):
        return os.path.join(self.path, 'reports')

    @property
    def report_prefix_path(self):
        return os.path.join(self.report_folder_path, self.name)

    def seed_report_data(self):
        '''Put meta data about this project into report'''
        logger.info('Seeding report data.')
        report_data['project'] = {
            'brainy_version': brainy_version,
            'name': self.name,
            'pipes': [],
        }
        #[MF]this function works with "create", if there is no YAML file, in the case of a fresh project,
        #[MF]it puts some inside using "write_project_config (contained in brainy.config.py)"
    def init(self, inherit_config={}, override_config={}):
        # Make project dir.
        if not os.path.exists(self.path):
            raise BrainyProjectError('Project folder does not exists: %s' %
                                     self.path)
        # Put basic YAML config during project creation. This is required for
        # project to be valid. We will also check version compatibility.
        write_project_config(self.path, inherit_config=inherit_config,
                             override_config=override_config)


        # [MF]This function "create" is the first one to be run by the deamon when a new 
        # [MF]project is given to process. Its goal: to create the .PIPE file (succession of YAML files)
        # [MF]that will define the workflow. This PIPE file is then evaluated by the "run" function
    def create(self, from_workflow='canonical', inherit_config={},
               override_config={}):
        # Make project dir.
        if not os.path.exists(self.path):
            logger.info('Creating new project folder: %s' % self.path)
            os.mkdir(self.path)
        else:
            raise BrainyProjectError('Project folder already exists: %s' %
                                     self.path)
        self.init(inherit_config=inherit_config,
                  override_config=override_config)
        # [MF]Put in the project a standard iBRAIN workflow (.PIPE) made of the different YAML files
        # [MF]described by the descriptor workflow_name. By default this workflow is called 'canonical'.
        bootstrap_workflow(self.path, workflow_name=from_workflow)

    def is_a_valid_project_folder(self):
        return project_has_config(self.path)

    def load_config(self):
        self.config = load_user_config() #[MF]in brainy.config.py, load the user's project descriptors
        project_config = load_project_config(self.path)#[MF]in brainy.config.py, load the project's workflow
        logger.info('Overwriting global configuration with project specific.')
        self.config = merge_dicts(self.config, project_config)

    def clean(self, manager_cls=PipesManager):
        '''Clean the project house.'''
        logger.info('<brainy rolls over the project to clean the house>')
        logger.info('Loading configuration')
        self.load_config()
        self.pipes = manager_cls(self)
        logger.info('Removing all the output data of every pipeline.')
        self.pipes.run('clean_pipelines_output')
        if os.path.exists(self.report_folder_path):
            logger.info('Removing all the reports in: %s' %
                        self.report_folder_path)
            shutil.rmtree(self.report_folder_path)
        logger.info('<Done>')

        # [MF] this function is the core of Brainy, looks at the .PIPE workflow made of loaded YAML files
        # [MF] and executes the tasks according to the YAML encoded protocol, through flag management
    def run(self, manager_cls=PipesManager, command='process_pipelines'):
        '''
        Load project configuration. Discover and process pipelines using the
        specified scheduler.
        '''
        logger.info('<brainy rolls over the project to {%s}>' % command)
        logger.info('Loading configuration')
        self.load_config()
        self.seed_report_data()
        logger.info('Initializing "%s" as a scheduling engine.' %
                    self.config['scheduling']['engine'])
        self.scheduler = BrainyScheduler.build_scheduler(
            self.config['scheduling']['engine'])
        self.pipes = manager_cls(self)
        self.pipes.run(command)
        logger.info('<Done>')
