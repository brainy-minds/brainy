'''
Basic routings for nose testing of brainy code.
'''
import re
import os
import sys
import tempfile
import unittest
from cStringIO import StringIO
# We include <root>/lib/python and point to tests/mock/root/etc/config
extend_path = lambda root_path, folder: sys.path.insert(
    0, os.path.join(root_path, folder))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
extend_path(ROOT, '')
extend_path(ROOT, 'lib/python')
import brainy.config
brainy.config.IBRAIN_ROOT = os.path.join(ROOT, 'tests', 'mock', 'root')
from brainy.pipes import PipesManager
from brainy.project import BrainyProject

print brainy.workflows.__file__
exit()

class MockProject(BrainyProject):

    def __init__(self, name):
        '''bootstrap test project folder in temporary path'''
        path = tempfile.mkdtemp()
        BrainyProject.__init__(self, name, path)


class MockPipesManager(PipesManager):

    def __init__(self, mock_pipe_yaml, pipe_name='mock_test'):
        self.project = MockProject('mock_project')
        # Bootstrap test project.
        self.project.create(from_workflow='empty')
        # Write the mock pipe content.
        with open(os.path.join(self.project_path, pipe_name + '.br'), 'w+') \
                as pipe_file:
            pipe_file.write(mock_pipe_yaml)
        # Overwrite the initialization.
        PipesManager.__init__(self, self.project)


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
        match = re.search('^Report file is written to:\s*([^\s\<]+)',
                          self.captured_output, re.MULTILINE)
        report_file = match.group(1)
        assert os.path.exists(report_file)
        return open(report_file).read()
