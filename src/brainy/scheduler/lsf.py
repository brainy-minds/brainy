from brainy.scheduler.base import (SHORT_QUEUE, NORM_QUEUE, LONG_QUEUE,
                                   PENDING_STATE, RUNNING_STATE, DONE_STATE,
                                   JOB_STATES, BrainyScheduler)
import logging
logger = logging.getLogger(__name__)


class NoLsfSchedulerFound(Exception):
    '''No LSF scheduler'''


class Lsf(BrainyScheduler):

    def __init__(self):
        self.bsub = None
        self.bjobs = None
        self.__bjobs_cache = None
        self.bkill = None
        self.init_scheduling()
        self.states_map = {
            PENDING_STATE: 'PEND',
            RUNNING_STATE: 'RUN',
            DONE_STATE: 'DONE',
        }

    def init_scheduling(self):
        try:
            from sh import bjobs as _bjobs, bsub as _bsub, bkill as _bkill
            self.bsub = _bsub
            self.bjobs = _bjobs
            self.bkill = _bkill
        except ImportError:
            exception = NoLsfSchedulerFound('Failed to locate LSF commands '
                                            'like bjobs, bsub, bkill. Is LSF '
                                            'installed?')
            logger.warn(exception)

    def bjobs(self, *args, **kwds):
        if not self.__bjobs_cache:
            self.__bjobs_cache = self._bjobs(*args, **kwds)
        return self.__bjobs_cache

    def submit_job(self, shell_command, queue, report_file):
        '''Submit job using *bsub* command.'''
        try:
            self.bsub(
                '-W', queue,
                '-o', report_file,
                shell_command,
            )
        except Exception as error:
            logger.exception(error)
            return 'Failed to submit new job: %s' % shell_command

        logger.info('Submitting new job: %s', shell_command)
        logger.info('Report file will be written to: %s' % report_file)
        return ('Submitting new job: "%s"\n' +
                'Report file will be written to: %s') % \
               (shell_command, report_file)

    def count_working_jobs(self, key=None):
        '''
        Find out how many jobs are both PENDING and RUNNING. Require job
        description to contain the **key** substring. If key is None,
        then no filtering is done.
        '''
        jobs_list = self.bjobs('-aw').split('\n')
        if len(jobs_list) == 0:
            raise Exception('Failed to run bjobs')
        elif len(jobs_list) == 1 and 'No job found' in jobs_list:
            return 0
        working_jobs = [job_info for job_info in jobs_list
                        if ' RUN ' in job_info or ' PEND ' in job_info]
        logger.debug('Total number of working jobs found: %d' %
                     len(working_jobs))
        if key is None:
            # No filtering is applied.
            filtered_jobs = working_jobs
        else:
            # Sieve only matched job info strings.
            filtered_jobs = [job_info for job_info in jobs_list
                             if key in job_info]
        return len(filtered_jobs)

    def list_jobs(self, states):
        assert all([(state in JOB_STATES) for state in states])
        # TODO: make pure python implementation for state filtering.
        return self.bjobs('-aw').split('\n')
