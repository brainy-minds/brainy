from brainy.utils import invoke
from brainy.process.base import BrainyProcess
from brainy.project.report import BrainyReporter


class CanCheckData(object):

    def has_data(self):
        '''
        Optionally call the method responsible for checking consistency of the
        data. Code is baked into a script and invoked in the shell. Method will
        interpret any output as error.
        '''
        if 'check_data_call' not in self.description:
            return
        bake_code = getattr(self, 'bake_%s_code' % self.code_language)
        script = bake_code(self.description['check_data_call'])
        (stdoutdata, stderrdata) = invoke(script)
        any_output = (stdoutdata + stderrdata).strip()
        if len(any_output) > 0:
            # Interpret any output as error.
            BrainyReporter.append_warning(
                message='Checking data consistency failed',
                output=any_output,
            )
        return True


class CodeProcess(BrainyProcess, CanCheckData):

    def __init__(self, code_language):
        BrainyProcess.__init__(self)
        self.code_language = code_language

    def submit(self):
        '''Default method for code submission'''
        submit_code_job = getattr(self, 'submit_%s_job' % self.code_language)
        get_code = getattr(self, 'get_%s_code' % self.code_language)

        submission_result = submit_code_job(get_code())
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
        CodeProcess.__init__(self, 'matlab')
        super(MatlabCodeProcess, self).__init__('matlab')


class PythonCodeProcess(CodeProcess):

    def __init__(self):
        super(PythonCodeProcess, self).__init__('python')
