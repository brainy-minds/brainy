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
from brainy.pipes import PipesModule


class MockPipesModule(PipesModule):

    def __init__(self, mock_pipe_json):
        env = self.bake_and_init_env()
        # Write the mock pipe content.
        with open(os.path.join(env['pipes_path'], 'mockPipe.json'), 'w+') \
                as pipe_file:
            pipe_file.write(mock_pipe_json)
        # Overwrite the initialization
        PipesModule.__init__(self, 'pipes', env)

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
