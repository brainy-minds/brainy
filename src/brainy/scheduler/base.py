import logging
logger = logging.getLogger(__name__)


# TODO: Queuing settings have to be configurable
SHORT_QUEUE = '1:00'
NORM_QUEUE = '8:00'
LONG_QUEUE = '36:00'


# Job states
PENDING_STATE = 1
RUNNING_STATE = 2
DONE_STATE = 3
JOB_STATES = [PENDING_STATE, RUNNING_STATE, DONE_STATE]


class BrainyScheduler(object):
    '''
    Base scheduling engine class. In general, scheduler is responsible for
    submitting, monitoring, killing and performing other job managing
    operations.
    '''

    @staticmethod
    def build_scheduler(name):
        '''Factory for scheduling engines.'''
        name = name.lower()
        if name == 'lsf':
            from brainy.scheduler.lsf import Lsf
            return Lsf()
        elif name == 'shellcmd':
            from brainy.scheduler.shellcmd import ShellCommand
            return ShellCommand()
        raise Exception('Unknown scheduler type: %s' % name)

