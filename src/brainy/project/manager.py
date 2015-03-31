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

logger = logging.getLogger(__name__)


class ProjectManager(object):

    def __init__(self, project_list_path):
        self.project_list_path = project_list_path

    def load_projects(self):
        '''Load/init a YAML file listing brainy projects'''
        if os.path.exists(self.project_list_path):
            # There is a non-empty list of registered projects.
            self.projects = load_yaml(open(self.project_list_path).read())
        else:
            # Project list is empty. Simply initialize it.
            self.projects = []
            with open(self.project_list_path, 'w+') as stream:
                stream.write(dump_yaml(self.projects))

    def build_projects(self):
        logger.info('Building brainy projects with no configs or workflows')

    def run_projects(self):
        logger.info('Running brainy projects')
