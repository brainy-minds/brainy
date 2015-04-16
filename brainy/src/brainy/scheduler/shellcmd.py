import logging
from brainy.utils import invoke
from brainy.scheduler.base import BrainyScheduler
from brainy.errors import BrainyProcessError
logger = logging.getLogger(__name__)


class ShellCommand(BrainyScheduler):
    '''
    "No scheduler" scheme will run commands as serial code. Useful for testing
    and optional fallback to local execution.
    '''

    def submit_job(self, shell_command, queue, report_file):
        # Invoke the shell command.
        (stdoutdata, stderrdata) = invoke(shell_command)
        # Produce a report output.
        with open(report_file, 'w+') as report:
            report.write('--CMD---' + '-' * 80 + '\n')
            report.write(shell_command)
            if len(stdoutdata) > 0:
                report.write('\n-STDOUT-' + '-' * 80 + '\n')
                report.write(stdoutdata)
            if len(stderrdata) > 0:
                report.write('\n-STDERR-' + '-' * 80 + '\n')
                report.write(stderrdata)
        # Fail submission if the child process ended up badly.
        if len(stderrdata) > 0:
            raise BrainyProcessError(
                message='Process job produced some error(s). ',
                output=stderrdata,
                job_report=report_file,
            )
        logger.info('Command was successfully executed: %s', shell_command)
        logger.info('Report file is written to: %s' % report_file)
        return ('Command was successfully executed: "%s"\n' +
                'Report file is written to: %s') % \
               (shell_command, report_file)

    def count_working_jobs(self, key):
        return 0

    def list_jobs(self, states):
        return list()
