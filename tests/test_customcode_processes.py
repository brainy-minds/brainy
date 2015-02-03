'''
Testing brainy.process.code.* classes that help to submit custom user code.

Usage example:
    nosetests -vv -x --pdb test_customcode_processes
'''
import os
from brainy_tests import MockPipesManager, BrainyTest
from testfixtures import LogCapture


def bake_a_mock_pipe_with_no_param():
    return MockPipesManager('''
{
    # Define iBRAIN pipe type
    "type": "CellProfiler.Pipe",
    # Define chain of processes
    "chain": [
        {
            "type": "CustomCode.PythonCall",
            "default_parameters": {
                "job_submission_queue": "8:00",
                "job_resubmission_queue": "36:00",
                "batch_path": "../../BATCH"
            }
        }
    ]
}
    \n''')


def bake_a_working_mock_pipe():
    return MockPipesManager('''
{
    # Define iBRAIN pipe type
    "type": "CellProfiler.Pipe",
    # Define chain of processes
    "chain": [
        {
            "type": "CustomCode.PythonCall",
            "submit_call": "print 'I am a mock custom python call'",
            "default_parameters": {
                "job_submission_queue": "8:00",
                "job_resubmission_queue": "36:00",
                "batch_path": "../../BATCH"
            }
        }
    ]
}
    \n''')


def bake_a_bash_pipe():
    return MockPipesManager('''
{
    # Define iBRAIN pipe type
    "type": "CellProfiler.Pipe",
    # Define chain of processes
    "chain": [
        {
            "type": "CustomCode.BashCall",
            "submit_call": "echo 'I am a mock custom bash call'",
            "default_parameters": {
                "job_submission_queue": "8:00",
                "job_resubmission_queue": "36:00",
                "batch_path": "../../BATCH"
            }
        }
    ]
}
    \n''')


def bake_a_matlab_pipe():
    return MockPipesManager('''
{
    # Define iBRAIN pipe type
    "type": "CellProfiler.Pipe",
    # Define chain of processes
    "chain": [
        {
            "type": "CustomCode.MatlabCall",
            "submit_call": "disp('I am a mock custom matlab call')",
            "default_parameters": {
                "job_submission_queue": "8:00",
                "job_resubmission_queue": "36:00"
            }
        }
    ]
}
    \n''')


def bake_pipe_with_matlab_user_path_extend():
    return MockPipesManager('''
{
    # Define iBRAIN pipe type
    "type": "CellProfiler.Pipe",
    # Define chain of processes
    "chain": [
        {
            "type": "CustomCode.MatlabCall",
            "submit_call": "disp(['Call result is: ' foo()])",
            "default_parameters": {
                "job_submission_queue": "8:00",
                "job_resubmission_queue": "36:00"
            }
        }
    ]
}
    \n''')


class TestCustomCode(BrainyTest):

    def test_python_call_missing_param(self):
        '''Test PythonCall: for "missing parameter" error'''
        self.start_capturing()
        # Run pipes.
        pipes = bake_a_mock_pipe_with_no_param()
        with LogCapture() as logs:
            pipes.process_pipelines()
        # Check output.
        self.stop_capturing()
        # print logs
        assert 'Missing "submit_call" key in YAML descriptor' \
            in str(logs)

    def test_a_basic_python_call(self):
        '''Test PythonCall: for basic submission'''
        self.start_capturing()
        # Run pipes.
        pipes = bake_a_working_mock_pipe()
        pipes.process_pipelines()
        # Check output.
        self.stop_capturing()
        # print self.captured_output
        # assert False
        assert 'I am a mock custom python call' in self.get_report_content()

    def test_a_basic_bash_call(self):
        '''Test BashCall: for basic submission'''
        self.start_capturing()
        # Run pipes.
        pipes = bake_a_bash_pipe()
        pipes.process_pipelines()
        # Check output.
        self.stop_capturing()
        # print self.captured_output
        # assert False
        assert 'I am a mock custom bash call' in self.get_report_content()

    def test_a_basic_matlab_call(self):
        '''Test MatlabCall: for basic submission'''
        self.start_capturing()
        # Run pipes.
        pipes = bake_a_matlab_pipe()
        pipes.process_pipelines()
        # Check output.
        self.stop_capturing()
        # print self.captured_output
        # assert False
        assert 'I am a mock custom matlab call' in self.get_report_content()

    def test_user_path_in_matlab_call(self):
        '''Test MatlabCall: if extending user path works'''
        self.start_capturing()
        # Run pipes.
        pipes = bake_pipe_with_matlab_user_path_extend()
        # Place new matlab function into extending location.
        lib_matlab_path = os.path.join(pipes.project.path,
                                       'lib', 'matlab')
        os.makedirs(lib_matlab_path)
        overwrite_func_path = os.path.join(lib_matlab_path, 'foo.m')
        with open(overwrite_func_path, 'w+') as func_file:
            func_file.write('''function res=foo()
res = 'foo';
end
            ''')
        pipes.process_pipelines()
        # Check output.
        self.stop_capturing()
        # print self.captured_output
        # assert False
        assert 'Call result is: foo' in self.get_report_content()
