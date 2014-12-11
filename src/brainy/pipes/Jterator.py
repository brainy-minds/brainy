import os
import re
from fnmatch import fnmatch, translate as fntranslate
from os.path import basename
from brainy.process import BrainyProcess, BrainyProcessError
from brainy.pipes import BrainyPipe
from brainy.pipes.Tools import get_timestamp_str


class Pipe(BrainyPipe):
    '''
    Jterator pipe includes steps like:
     - Create job list and pre-cluster (run the first job of the pipeline)
     - RunInParallel
     - MergeResults
    '''


class PreCluster(BrainyProcess):
    '''Create job list and Jterate over the first job'''


class RunInParallel(BrainyProcess):
    '''Jterate over the rest of jobs in parallel'''


class MergeResults(BrainyProcess):
    '''Merge/reduce output results by job'''
