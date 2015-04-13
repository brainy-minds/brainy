import logging
from brainy.pipes.base import BrainyPipe
from brainy.process.code import (BashCodeProcess, MatlabCodeProcess,
                                 PythonCodeProcess, ParallelCall)

logger = logging.getLogger(__name__)


class CustomPipe(BrainyPipe):
    '''
    CustomPipe is a stub to supervise running of custom user code processes.
    '''


class BashCall(BashCodeProcess, ParallelCall):
    '''Bake and call bash as a single job.'''

    def get_bash_code(self):
        return self.call


class MatlabCall(MatlabCodeProcess, ParallelCall):
    '''Bake and call python as a single job.'''

    def get_matlab_code(self):
        return self.call


class PythonCall(PythonCodeProcess, ParallelCall):
    '''Bake and call python as a single job.'''

    def get_python_code(self):
        return self.call
