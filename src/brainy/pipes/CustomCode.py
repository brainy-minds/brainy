import logging
from brainy.utils import load_yaml, invoke
from brainy.errors import BrainyProcessError
from brainy.project.report import BrainyReporter
from brainy.pipes.base import BrainyPipe
from brainy.process.code import (BashCodeProcess, MatlabCodeProcess,
                                 PythonCodeProcess)
from brainy.process.decorator import (format_with_params,
                                      require_key_in_description)

logger = logging.getLogger(__name__)


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

    def is_parallel(self):
        return 'foreach' in self.description

    @property
    def foreach(self):
        return self.description['foreach']

    def eval_foreach_values(self):
        '''
        Evals value of `foreach->in` statement using YAML or any know language.
        Returns a list of strings that would be value for `foreach` section.
        '''
        statement = self.foreach['in']
        # By default use YAML as `in` statement.
        language = self.foreach.get('using', 'yaml').lower()
        if language == 'yaml':
            return load_yaml(statement)
        # Else, bake the script for usual brainy environment.
        bake_code = getattr(self, 'bake_%s_code' % language.lower())
        logger.debug('Evaluating `foreach-in` statement: %s' % statement)
        script = bake_code(statement)
        logger.debug('Baked `foreach-in` script to invoke: %s' % script)
        (stdoutdata, stderrdata) = invoke(script)
        error_output = stderrdata.strip()
        if error_output:
            # Interpret error output as error.
            BrainyReporter.append_warning(
                message='Evaluating foreach `in` values failed.',
                output=error_output,
            )
        values = '\n'.split((stdoutdata).strip())
        if not values:
            BrainyReporter.append_warning(
                message='Section `foreach->in` returned an empty list.',
                output='Foreach in: %s' % statement,
            )
        return values

    def paralell_submit(self, submit_single_job):
        # Do single job if `foreach` section is missing.
        if not self.is_parallel():
            logger.info('Submitting call as a single job')
            submit_single_job()
            return
        logger.info('`Foreach` statement found.')
        logger.info('Submitting multiple jobs in parallel.')
        # Validate `foreach` section keys.
        for key in ['var', 'in']:
            if key not in self.foreach:
                raise BrainyProcessError(
                    ('Missing "%s" key in foreach section of the YAML ' +
                     'descriptor of the process.') %
                    key
                )
        var_name = self.foreach['var']
        if var_name in self.format_parameters:
            raise BrainyProcessError(
                ('Variable name in foreach section of the YAML ' +
                 'descriptor of the process overlaps with reserved ' +
                 'parameter names: %s') %
                var_name
            )
        # Do actual parallel submission.
        self.format_parameters.append(var_name)  # Allow call customization.
        values = self.eval_foreach_values()
        logger.debug(values)
        for index, value in enumerate(values, start=1):
            logger.info('In-a-loop iteration (#%d): {%s} -> {%s}' %
                        (index, var_name, value))
            #  Assign variable value.
            setattr(self, var_name, value)
            self.report_name_postfix = str(index)
            # Clean process templates compilation cache.
            # TODO: put process templates logic into a separate class.
            for clean_var in [var_name, 'call']:
                if clean_var in self.compiled_params:
                    del self.compiled_params[clean_var]
            # Submit the job.
            submit_single_job()


class BashCall(BashCodeProcess, Parallel):
    '''Bake and call bash as a single job.'''

    def get_bash_code(self):
        return self.call

    def submit(self):
        submit_single_job = super(BashCall, self).submit
        self.paralell_submit(submit_single_job)

    def resubmit(self):
        resubmit_single_job = super(BashCall, self).resubmit
        self.paralell_submit(resubmit_single_job)


class MatlabCall(MatlabCodeProcess, Parallel):
    '''Bake and call python as a single job.'''

    def get_matlab_code(self):
        return self.call

    def submit(self):
        submit_single_job = super(MatlabCall, self).submit
        self.paralell_submit(submit_single_job)

    def resubmit(self):
        resubmit_single_job = super(MatlabCall, self).resubmit
        self.paralell_submit(resubmit_single_job)


class PythonCall(PythonCodeProcess, Parallel):
    '''Bake and call python as a single job.'''

    def get_python_code(self):
        return self.call

    def submit(self):
        submit_single_job = super(PythonCall, self).submit
        self.paralell_submit(submit_single_job)

    def resubmit(self):
        resubmit_single_job = super(PythonCall, self).resubmit
        self.paralell_submit(resubmit_single_job)
