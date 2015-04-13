import logging
from brainy.utils import invoke, load_yaml
from brainy.errors import BrainyProcessError
from brainy.process.base import BrainyProcess
from brainy.project.report import BrainyReporter
from brainy.process.decorator import (format_with_params,
                                      require_key_in_description)

logger = logging.getLogger(__name__)


class CanCheckData(object):

    def has_data(self):
        '''
        Optionally call the method responsible for checking consistency of the
        data. Code is baked into a script and invoked in the shell. Method will
        interpret any output as error.
        '''
        if 'check_data' not in self.description:
            return False
        bake_code = getattr(self, 'bake_%s_code' % self.code_language)
        script = bake_code(self.description['check_data'])
        (stdoutdata, stderrdata) = invoke(script)
        any_output = (stdoutdata + stderrdata).strip()
        if len(any_output) > 0:
            # Interpret any output as error.
            BrainyReporter.append_warning(
                message='Checking data consistency failed',
                output=any_output,
            )
        return True


class Explained(object):
    '''
    Require user to document the processes.
    '''

    @property
    @format_with_params
    @require_key_in_description
    def doc(self):
        '''
        Documentation put into detailed reports as brainy progresses
        with project execution.
        '''


class CodeProcess(BrainyProcess, CanCheckData, Explained):

    def __init__(self, code_language):
        BrainyProcess.__init__(self)
        self.code_language = code_language

    def submit(self):
        '''Default method for code submission'''
        submit_code_job = getattr(self, 'submit_%s_job' % self.code_language)
        get_code = getattr(self, 'get_%s_code' % self.code_language)

        submission_result = submit_code_job(get_code())
        logger.debug('Submission result:\n%s' % submission_result)
        BrainyReporter.append_message(
            message='Submitting new job',
            output=submission_result
        )

        self.set_flag('submitted')

    def resubmit(self):
        submit_code_job = getattr(self, 'submit_%s_job' % self.code_language)
        get_code = getattr(self, 'get_%s_code' % self.code_language)

        resubmission_result = submit_code_job(get_code(), is_resubmitting=True)
        BrainyReporter.append_message(
            message='Resubmitting job',
            output=resubmission_result
        )

        self.set_flag('resubmitted')
        BrainyProcess.resubmit(self)


class BashCodeProcess(CodeProcess):

    def __init__(self):
        super(BashCodeProcess, self).__init__('bash')


class MatlabCodeProcess(CodeProcess):

    def __init__(self):
        super(MatlabCodeProcess, self).__init__('matlab')


class PythonCodeProcess(CodeProcess):

    def __init__(self):
        super(PythonCodeProcess, self).__init__('python')


class Callable(CodeProcess):
    '''
    Run a piece of custom code given by user in self.description['call'].
    '''

    @property
    @format_with_params
    @require_key_in_description
    def call(self):
        '''Main code to be submitted as a job.'''


class ParallelCall(Callable):
    '''Implementing foreach calls as parallel.'''

    def is_parallel(self):
        '''Do single job if `foreach` section is missing.'''
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
        compiled_statement = self.format_with_params(
            'compiled_statement', statement)
        # By default use YAML as `in` statement.
        language = self.foreach.get('using', 'yaml').lower()
        if language == 'yaml':
            return load_yaml(statement)
        # Else, bake the script for usual brainy environment.
        bake_code = getattr(self, 'bake_%s_code' % language.lower())
        logger.debug('Evaluating `foreach-in` statement: %s' %
                     compiled_statement)
        script = bake_code(compiled_statement)
        logger.debug('Baked `foreach-in` script to invoke: %s' % script)
        (stdoutdata, stderrdata) = invoke(script)
        error_output = stderrdata.strip()
        if error_output:
            # Interpret error output as error.
            BrainyReporter.append_warning(
                message='Evaluating foreach `in` values failed.',
                output=error_output,
            )
        # NEWLINE is a separator between values
        values = stdoutdata.strip().split('\n')
        logger.info('Looping over %d value(s).' % len(values))
        if len(stdoutdata.strip()) == 0 or not values:
            BrainyReporter.append_warning(
                message='Section `foreach->in` returned an empty list.',
                output='Foreach in: %s' % statement,
            )
            logger.warn('Empty foreach-in list for script:\n %s' % script)
            return []
        return values

    def paralell_submit(self, do_resubmit=False):
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
            if do_resubmit:
                Callable.resubmit(self)
            else:
                Callable.submit(self)

    def submit(self):
        if not self.is_parallel():
            logger.info('Submitting call as a single job')
            Callable.submit(self)
            return
        self.paralell_submit()

    def resubmit(self):
        if not self.is_parallel():
            logger.info('Resubmitting call as a single job')
            Callable.resubmit(self)
            return
        self.paralell_submit(do_resubmit=True)
