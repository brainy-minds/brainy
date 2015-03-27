from brainy.pipes.base import BrainyPipe
from brainy.process.code import (BashCodeProcess, MatlabCodeProcess,
                                 PythonCodeProcess)
from brainy.process.decorator import (format_with_params,
                                      require_key_in_description)


class CustomPipe(BrainyPipe):
    '''
    CustomPipe is a stub to supervise running of custom user code processes.
    '''


class Submittable(object):
    '''
    Run a piece of custom code given by user in self.description[submit_call].
    '''

    @property
    @format_with_params
    @require_key_in_description
    def call(self):
        'Main code to be submitted as a job.'


class Parallel(Submittable):
    '''Implementing foreach calls as parallel.'''

    # def is_parallel(self):
    #     return 'foreach' in self.description

    # # def get_

    # def submit(self):
    #     submit_single_job = super(ParallelCall, self).submit
    #     for


class BashCall(BashCodeProcess, Parallel):
    '''Bake and call bash as a single job.'''

    def get_bash_code(self):
        return self.call


class MatlabCall(MatlabCodeProcess, Parallel):
    '''Bake and call python as a single job.'''

    def get_matlab_code(self):
        return self.call


class PythonCall(PythonCodeProcess, Parallel):
    '''Bake and call python as a single job.'''

    def get_python_code(self):
        return self.call
