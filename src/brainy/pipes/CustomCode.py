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
    def submit_call(self):
        'Main code to be submitted.'


class BashCall(BashCodeProcess, Submittable):
    '''Bake and call bash as a single job.'''

    def get_bash_code(self):
        return self.submit_call


class MatlabCall(MatlabCodeProcess, Submittable):
    '''Bake and call python as a single job.'''

    def get_matlab_code(self):
        return self.submit_call


class PythonCall(PythonCodeProcess, Submittable):
    '''Bake and call python as a single job.'''

    def get_python_code(self):
        return self.submit_call


# class MapPython(JsonProcess):
#
#     @property
#     def map(self):
#         bake_code = getattr(self, 'bake_%s_code' % self.code_language)
#         script = bake_code(self.map_call)
#         return json.loads(invoke(script))
#
# class Reduce(object):
#     pass
