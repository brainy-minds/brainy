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
extend_path(ROOT, 'src')
from brainy.config import BRAINY_USER_CONFIG_TPL
from brainy.workflows import WorkflowLocations
from brainy.project.base import BrainyProject
from brainy.pipes.manager import PipesManager
from brainy.scheduler import BrainyScheduler
from brainy.log import setup_logging
setup_logging('silent')  # Otherwise output capturing will not work


class MockProject(BrainyProject):

    def __init__(self, name, brainy_config):
        '''bootstrap test project folder in temporary path'''
        path = tempfile.mkdtemp()
        workflow_locations = WorkflowLocations(brainy_config)
        BrainyProject.__init__(self, name, path, workflow_locations)
        self.seed_report_data()


class MockPipesManager(PipesManager):

    def __init__(self, mock_pipe_yaml, pipe_name='mock_test'):
        brainy_config = yaml.load(BRAINY_USER_CONFIG_TPL)
        # Bootstrap test project.
        override_config = {
        }
        self.project = MockProject('mock_project', brainy_config)
        self.project.create(from_workflow='empty',
                            inherit_config=brainy_config,
                            override_config=override_config)

        self.project.load_config(brainy_config)
        self.project.scheduler = BrainyScheduler.build_scheduler(
            self.project.config['scheduling']['engine'])

        # Write the mock pipe content.
        if type(mock_pipe_yaml) == dict:
            mock_pipe_yaml = yaml.dump(mock_pipe_yaml, default_flow_style=True)
        test_pipe_filepath = os.path.join(self.project_path, pipe_name + '.br')
        with open(test_pipe_filepath, 'w+') as pipe_file:
            pipe_file.write(mock_pipe_yaml)

        # Overwrite the initialization.
        PipesManager.__init__(self, self.project)


class BrainyTest(unittest.TestCase):
    '''Extended this class for brainy testing'''

    def __init__(self, methodName='runTest'):
        super(BrainyTest, self).__init__(methodName)
        self.captured_output = None
        self.captured_error = None
        self.__first_baked_process = None

    def start_capturing(self):
        # Start output capturing.
        self.captured_output = None
        self.__old_stdout = sys.stdout
        sys.stdout = self.__stdout = StringIO()
        self.captured_error = None
        self.__old_stderr = sys.stderr
        sys.stderr = self.__stderr = StringIO()

    def stop_capturing(self):
        # Stop output capturing.
        if self.captured_output is None:
            self.captured_output = self.__stdout.getvalue()
        sys.stdout = self.__old_stdout
        # Stop error capturing.
        if self.captured_error is None:
            self.captured_error = self.__stderr.getvalue()
        sys.stderr = self.__old_stderr

    def setup(self):
        # Make sure pipette is not waiting forever for the input.
        self.__old_stdin = sys.stdin
        sys.stdin = StringIO()
        # self.start_capturing()

    def teardown(self):
        # Restore the standard input.
        sys.stdin = self.__old_stdin
        # self.stop_capturing()

    def get_report_content(self, output=None):
        if output is None:
            output = self.captured_output
        match = re.search('\s*Report file is written to:\s*([^\s\<]+)',
                          output, re.MULTILINE)
        report_file = match.group(1)
        assert os.path.exists(report_file)
        return open(report_file).read()

    def get_first_process(self, pipes):
        '''
        Takes pipe manager and returns a first baked process instance.
        Can be useful for mocking around.
        '''
        if self.__first_baked_process is None:
            for pipeline in pipes.pipelines:
                for process in pipeline.bake_processes():
                    process.parameters.update(
                        pipeline.get_process_parameters(),
                    )
                    self.__first_baked_process = process
            if self.__first_baked_process is None:
                raise Exception('Failed to bake a process for mocking'
                                ' using given pipe manager')
        return self.__first_baked_process
