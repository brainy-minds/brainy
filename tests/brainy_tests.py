'''
Basic routings for nose testing of brainy code.
'''
from __future__ import unicode_literals
import re
import os
import sys
import yaml
import tempfile
import unittest
from cStringIO import StringIO
# We include <root>/lib/python and point to tests/mock/root/etc/config
extend_path = lambda root_path, folder: sys.path.insert(
    0, os.path.join(root_path, folder))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
extend_path(ROOT, '')
extend_path(ROOT, 'lib/python')
# import brainy.config
# brainy.config.IBRAIN_ROOT = os.path.join(ROOT, 'tests', 'mock', 'root')
from brainy.config import (BRAINY_PROJECT_CONFIG_TPL, BRAINY_USER_CONFIG_TPL,
                           write_project_config)
from brainy.utils import merge_dicts
from brainy.project import BrainyProject
from brainy.pipes import BrainyPipe, PipesManager
from brainy.scheduler import BrainyScheduler


class MockProject(BrainyProject):

    def __init__(self):
        super(MockProject, self).__init__('mock', tempfile.mkdtemp())
        assert not os.path.exists(self.path)
        os.makedirs(self.path)
        self.write_mock_project_config()
        self.load_config()
        self.scheduler = BrainyScheduler.build_scheduler(
            self.config['scheduling']['engine'])

    def load_config(self):
        # Overwrite with mock config which a usual nested dictionary.
        user_config_tpl = yaml.load(StringIO(BRAINY_USER_CONFIG_TPL))
        super(MockProject, self).load_config()
        self.config = merge_dicts(user_config_tpl, self.config)

    def write_mock_project_config(self):
        write_project_config(self.path)


class MockPipe(BrainyPipe):

    def __init__(self, pipes_manager, mock_pipe_json):
        # env = self.bake_and_init_env()
        # Overwrite the initialization
        super(MockPipesModule, self).__init__(pipes_manager, mock_pipe_json)

    def bake_and_init_env(self):
        project_dir = tempfile.mkdtemp()
        env = {
            'plate_path': project_dir,
            'tiff_path': os.path.join(project_dir, 'TIFF'),
            'batch_path': os.path.join(project_dir, 'BATCH'),
            'postanalysis_path': os.path.join(project_dir, 'POSTANALYSIS'),
            'jpg_path': os.path.join(project_dir, 'JPG'),
            'pipes_path': os.path.join(project_dir, 'PIPES'),
        }
        for key in env:
            if not key.endswith('path') or os.path.exists(env[key]):
                continue
            os.makedirs(env[key])
        return env


class MockPipesManager(PipesManager):
    pass


def build_pipes(mock_pipe_json):
    project = MockProject()
    # Write the mock pipe content.
    with open(os.path.join(project.path, 'mock.br'), 'w+') \
            as pipe_file:
        pipe_file.write(mock_pipe_json)
    pipes = MockPipesManager(project)
    return pipes


class BrainyTest(unittest.TestCase):
    '''Extended this class for brainy testing'''

    def __init__(self, methodName='runTest'):
        super(BrainyTest, self).__init__(methodName)
        self.captured_output = None

    def start_capturing_output(self):
        # Start output capturing.
        self.captured_output = None
        self.__old_stdout = sys.stdout
        sys.stdout = self.__stdout = StringIO()

    def stop_capturing_output(self):
        if self.captured_output is None:
            self.captured_output = self.__stdout.getvalue()
        # Stop output capturing.
        sys.stdout = self.__old_stdout

    def setup(self):
        # Make sure pipette is not waiting forever for the input.
        self.__old_stdin = sys.stdin
        sys.stdin = StringIO()
        # self.start_capturing_output()

    def teardown(self):
        # Restore the standard input.
        sys.stdin = self.__old_stdin
        # self.stop_capturing_output()

    def get_report_content(self):
        # raise Exception(self.captured_output)
        match = re.search('^Report file is written to:\s*([^\s\<]+)',
                          self.captured_output, re.MULTILINE)
        report_file = match.group(1)
        assert os.path.exists(report_file)
        return open(report_file).read()
