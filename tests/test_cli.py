'''
Test command line interface (CLI) of brainy as it is integrated in shell.
Like this we want to guarantee that brainy shell commands do not break.
'''
from sh import brainy as brainy_shell
from unittest import TestCase
import tempfile


class CliTest(TestCase):

    def setUp(self):
        self.prefix_path = tempfile.mkdtemp()

    def test_demo(self):
        '''
        Test project create and project run.
        '''
        # Create
        output = brainy_shell.project('create',
                                      '-p', self.prefix_path,
                                      'demo',
                                      '--from=demo')
        print output.stderr
        print output.stdout
        assert output.exit_code == 0
        # Run
        output = brainy_shell.project('run',
                                      '-p', self.prefix_path)
        print output.stderr
        print output.stdout
        assert output.exit_code == 0
