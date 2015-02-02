import os
import re
from brainy_tests import BrainyTest
from brainy.scheduler import BrainyScheduler
from brainy.scheduler.lsf import NoLsfSchedulerFound, Lsf


MOCK_BJOBS_FILEPATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'mock', 'schedulers', 'ibrain_bjobs',
)


class GrayBoxedLsf(Lsf):
    '''
    Modify Lsf() to suite the testing needs.
    '''

    def mocked_bjobs(self, *args, **kwds):
        return open(MOCK_BJOBS_FILEPATH).read()

    def mocked_empty_bjobs(self, *args, **kwds):
        return 'No job found'

    def init_scheduling(self):
        self.bjobs = self.mocked_bjobs


class TestCustomCode(BrainyTest):

    def test_lsf_jobs_listing(self):
        scheduler = GrayBoxedLsf()
        #print scheduler.bjobs()
        assert 'RUN' in scheduler.bjobs()
        assert scheduler.count_working_jobs(None) > 0
        key = 'Data__Users__Markus__AntioxScreen'
        assert scheduler.count_working_jobs(key) > 0
