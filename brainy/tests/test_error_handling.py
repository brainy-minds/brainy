from brainy_tests import BrainyTest
from brainy.errors import check_for_known_error, KnownError


class TestErrorHandling(BrainyTest):

    def test_error_handling(self):
        '''Test how we handle errors by parsing logs'''
        log_text_with_error = '''
on.mat
HDF5-DIAG: Error detected in HDF5 (1.8.6) thread 0:
#000: H5F.c line 1509 in H5Fopen(): unable to open file
major: File accessability
minor: Unable to open file
#1: H5F.c line 1300 in H5F_open(): unable to read superblock
major: File accessability
        '''
        try:
            check_for_known_error(log_text_with_error)
        except KnownError as error:
            assert 'Error loading HDF5 file' in str(error)
        else:
            raise Exception('Failed to catch the expected exception.')

