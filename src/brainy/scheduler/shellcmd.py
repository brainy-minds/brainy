from brainy.utils import invoke
from brainy.scheduler.base import BrainyScheduler


class ShellCommand(BrainyScheduler):
    '''
    "No scheduler" scheme will run commands as serial code. Useful for testing
    and optional fallback to local execution.
    '''

    def submit_job(self, shell_command, queue, report_file):
        with open(report_file, 'w+') as output:
            output.write(invoke(shell_command))
        return ('Command was successfully executed: "%s"\n' +
                'Report file is written to: %s') % \
               (shell_command, report_file)

    def count_working_jobs(self, key):
        return 0

    def list_jobs(self, states):
        return list()
