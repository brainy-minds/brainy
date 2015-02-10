from brainy.utils import invoke
from brainy.scheduler.base import BrainyScheduler


class ShellCommand(BrainyScheduler):
    '''
    "No scheduler" scheme will run commands as serial code. Useful for testing
    and optional fallback to local execution.
    '''

    def submit_job(self, shell_command, queue, report_file):
        with open(report_file, 'w+') as report:
            report.write('--CMD---' + '-' * 80 + '\n')
            report.write(shell_command)
            (stdoutdata, stderrdata) = invoke(shell_command)
            if len(stdoutdata) > 0:
                report.write('-STDOUT-' + '-' * 80 + '\n')
                report.write(stdoutdata)
            if len(stderrdata) > 0:
                report.write('-STDERR-' + '-' * 80 + '\n')
                report.write(stderrdata)
        return ('Command was successfully executed: "%s"\n' +
                'Report file is written to: %s') % \
               (shell_command, report_file)

    def count_working_jobs(self, key):
        return 0

    def list_jobs(self, states):
        return list()
