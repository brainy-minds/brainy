'''
Integration between iBRAIN and brainy.

'''
import os
import re
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
from brainy.flags import FlagManager
from brainy.config import get_config
from brainy.scheduler import (BrainyScheduler, SHORT_QUEUE, LONG_QUEUE,
                              NORM_QUEUE)


class BrainyModule(FlagManager):

    def __init__(self, name, env):
        self.name = name
        # Check for missing values?
        self.env = env
        self.__results = None
        # At this points the iBRAIN ROOT has to be configured: set externally
        # or guessed.
        brainy_config = get_config()
        logger.info('Initializing "%s" as scheduling engine' %
                    brainy_config['scheduling_engine'])
        self.scheduler = BrainyScheduler.build_scheduler(
            brainy_config['scheduling_engine'])

    def _get_flag_prefix(self):
        return os.path.join(self.env['project_dir'], self.name)

    def get_results(self):
        if self.__results is None:
            # Find result files only once.
            results_regex = re.compile('%s_\d+.results' % self.name)
            self.__results = [filename for filename
                              in os.listdir(self.env['batch_dir'])
                              if results_regex.search(filename)]
        return self.__results

    def submit_job(self, script, queue=SHORT_QUEUE):
        results_file = os.path.join(self.env['batch_dir'], '%s_%s.results') % \
            (self.name, datetime.now().strftime('%y%m%d%H%M%S'))
        self.scheduler.submit_job(script, queue, results_file)

    @property
    def results_count(self):
        return len(self.get_results())

    def job_count(self, needle=None):
        if needle is None:
            needle = os.path.basename(self.env['project_dir'])
        return self.scheduler.count_working_jobs(needle)
