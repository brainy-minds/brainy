'''
Test command line interface (CLI) of brainy as it is integrated in shell.
Like this we want to guarantee that brainy shell commands do not break.
'''
import os
from sh import brainy as brainy_shell
from brainy_tests import BrainyTest
import tempfile


class CliTest(BrainyTest):

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
        # print self.captured_output
        # print output.stderr
        # print output.stdout
        assert output.exit_code == 0
        assert 'Bootstrapping project' in output.stderr
        assert '<Done>' in output.stderr
        assert 'ERROR' not in output.stderr

        # Run
        output = brainy_shell.project('run',
                                      '-p', os.path.join(self.prefix_path,
                                                         'demo'))
        print output.stderr
        print output.stdout
        assert output.exit_code == 0
        assert 'ERROR' not in output.stderr
