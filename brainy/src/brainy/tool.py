#!/usr/bin/env python2.7
'''
iBRAINTool is helper command line utility class for simplifying handling of
iBRAIN project flags, files, etc. This includes basic operations like refresh
the project modification date or restarting the modules.

Requires PyPlato: https://github.com/ewiger/plato
sudo easy_install PyPlato

This code is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Authors:
    Yauhen Yakimovich <eugeny.yakimovitch@gmail.com>,

Copyright (c) 2013 Pelkmans' Lab http://www.pelkmanslab.org/

    Installation
    ============

    Linux (Ubuntu)
    --------------

Use *easy_install* tool in command line:

    sudo easy_install PyPlato

or if you don't have a super-user access

    pip install --user PyPlato


'''
from __future__ import print_function
import os
import re
import sys
import argparse
import shutil
import logging
from plato.shell.findutils import (Match, find_files)
from fnmatch import fnmatch


__version__ = '0.1.1'

DRY_RUN = False
#DRY_RUN = True

VERBOSITY_LEVELS = {
    0: logging.NOTSET,
    1: logging.WARN,
    2: logging.INFO,
    3: logging.DEBUG,
}

# Note that flags support fnmatch format
RESTART_MODULES = {
    'tiff2png': {
        'project_files': [
            'ConvertAllTiff2Png.submitted',
        ],
        'batch_files': [
            'batch_png_convert_*',
            'ConvertAllTiff2Png_batch_png_convert_*_*.results',
        ],
    },
    'illcor': {
        'project_files': [
            'IllumCorrection_batch_illcor_*.submitted',
            'IllumCorrectionSettingsFileCreation.submitted',
        ],
        'batch_files': [
            'IllumCorrection_batch_illcor*.results',
            'Measurements_batch_illcor_*.mat',
            'batch_illcor_*.mat',
            'illuminationcorrection.complete',
        ],
    },
    'svm': {
        'project_files': [
            'SVMClassification_SVM_*.submitted',
            'SVMClassification_SVM_*.resubmitted',
            'SVMClassification_SVM_*.runlimit',
        ],
        'batch_files': [
            'SVMClassification_SVM_*.results',
            # Also kills results!
            'Measurements_SVM_*.mat',
        ],
    },
    'precluster': {
        'project_files': [
            'PreCluster.submitted',
            'PreCluster.resubmitted',
            'PreCluster.runlimit',
        ],
        'batch_files': [
            'PreCluster_*.results',
        ],
    },
    # Reset batch jobs step
    'batchjobs': {
        'project_files': [
            'SubmitBatchJobs.resubmitted',
            'SubmitBatchJobs.submitted',
        ],
        'batch_files': [
            'Batch_*_OUT.mat',
            'Batch_*_to_*_Measurements_*.mat',
            re.compile('Batch_\d+_to_\d+\.mat'),
            re.compile('Batch_\d+_to_\d+\.txt'),
            'Batch_*_to_*_*_*.results',
        ],
    },
    'celltype-overview': {
        'project_files': [
            'CreateCellTypeOverview.submitted',
            'CreateCellTypeOverview.resubmitted',
        ],
        'batch_files': [
            'CreateCellTypeOverview_*.results',
        ],
    },
    'fusion': {
        'project_files': [
        ],
        'batch_files': [
            'DataFusion_Measurements_*.results',
        ],
    },
    'pop-context': {
        'project_files': [
        ],
        'batch_files': [
            'getLocalCellDensityPerWell_auto_*.results',
        ],
    },
    'stich-seg': {
        'project_files': [
        ],
        'batch_files': [
            'StitchSegmentationPerWell_*.results',
        ],
    },
    'plate-overview': {
        'project_files': [
            'CreatePlateOverview.submitted',
        ],
        'batch_files': [
            'CreatePlateOverview_*.results',
        ],
    },
}


# Resume work on those actions. This is similar to restart but does not kills
# previous results in .MAT files.
RESUBMIT_MODULES = {
    'batchjobs': {
        'project_files': [
            'CreateCellTypeOverview.submitted',
            'CreateCellTypeOverview.resubmitted',
        ],
    },
    'svm': {
        'project_files': [
            'SVMClassification_SVM_*.submitted',
            'SVMClassification_SVM_*.resubmitted',
            'SVMClassification_SVM_*.runlimit',
        ],
        'batch_files': [
            'SVMClassification_SVM_*.results',
        ],
    },
}

RESUBMIT_CHOICES = list(RESUBMIT_MODULES.keys())

RESTART_CHOICES = list(RESTART_MODULES.keys()) + ['project']


# Kill those files to get a semi-"vanilla" state of the project
RESET_LIST = {
    'project': {
        'project_files': [
            '*.submitted',
            '*.resubmitted',
            'iBRAIN_Stage_1.completed',
            'FuseBasicData_*.results',
            'BASICDATA*',
            'ADVANCEDDATA*.mat',
        ],
        'project_folders': [
            'BATCH',
            'JPG',
            'POSTANALYSIS',
            'SEGMENTATION*',
        ],
    }
}


def resolve_filenames(patterns, parent_path, recursive=False, filetype='f'):
    '''
    Files can be a list of filenames, fnmatch patterns or regexps

    >>> len(resolve_filenames(['*'], '/tmp/a')) > 0
    True
    '''
    if not os.path.exists(parent_path):
        raise Exception('Failed to resolve: ' + parent_path)
    resolved = list()
    for pattern in patterns:
        # We look only into files for now.
        match = Match(filetype=filetype, name=pattern)
        resolved.extend([fname for fname
                        in find_files(parent_path, match,
                        recursive=recursive)])
    return resolved


class iBRAINToolError(Exception):
    '''Logical error thrown by iBRAINTool'''


class iBRAINTool(object):
    '''
    iBRAINTool is helper utility class for iBRAIN project.

    Any existing folder containing a TIFF is considered to be a valid
    project folder

    >>> project_dir = '/tmp/Project'
    ... os.makedirs(os.path.join(project_dir, '/TIFF'))
    ... tool = iBRAINTool(project_dir)
    '''
    def __init__(self, project_dir, is_multiplate, verbose=logging.INFO):
        logging.basicConfig(format='%(message)s', level=verbose)
        self.logger = logging.getLogger('iBRAINTool')
        if not self.is_project_dir(project_dir, is_multiplate):
            raise iBRAINToolError('Path is not a valid project folder: %s' %
                                  project_dir)
        self.logger.debug('iBRAINTool v%s', __version__)
        self.project_dir = project_dir
        self.is_multiplate = is_multiplate
        self.is_verbose = verbose
        self.__batch_listing = None

    def is_project_dir(self, path, is_multiplate):
        if not os.path.exists(path):
            raise IOError('Path does not exists: %s' %
                          path)
        if is_multiplate:
            return len(self.find_plate_names(path)) > 0
        else:
            return self.is_plate_dir(path)

    def find_plate_names(self, path):
        return [name for name in os.listdir(path)
                if self.is_plate_dir(os.path.join(path, name))]

    def is_plate_dir(self, path):
        tiff_path = os.path.join(path, 'TIFF')
        nikon_path = os.path.join(path, 'NIKON')
        return any(os.path.exists(plate_path) and os.path.isdir(plate_path)
                   for plate_path in (tiff_path, nikon_path))

    @property
    def batch_dir(self):
        return os.path.join(self.project_dir, 'BATCH')

    def kill_files(self, files):
        for filepath in files:
            if not DRY_RUN:
                print('Killing ' + filepath)
                os.unlink(filepath)
            else:
                print('Will kill ' + filepath)

    def kill_folders(self, folders):
        for folderpath in folders:
            if not DRY_RUN:
                print('Recursively killing ' + folderpath)
                shutil.rmtree(folderpath)
            else:
                print('Will recursively kill ' + folderpath)

    def restart_module(self, modulename):
        self.logger.info('Restarting module \'%s\' in project: %s' %
                         (modulename, self.project_dir))
        if not modulename in RESTART_MODULES:
            raise iBRAINToolError('Unknown module')
        module = RESTART_MODULES[modulename]
        project_files = resolve_filenames(
            module.get('project_files', []), self.project_dir)
        self.kill_files(project_files)
        batch_files = resolve_filenames(
            module.get('batch_files', []), self.batch_dir)
        self.kill_files(batch_files)
        self.restart_project()

    def resubmit_module(self, modulename):
        self.logger.info('Resubmitting module \'%s\' in project: %s' %
                         (modulename, self.project_dir))
        if not modulename in RESUBMIT_MODULES:
            raise iBRAINToolError('Unknown module')
        module = RESUBMIT_MODULES[modulename]
        project_files = resolve_filenames(
            module.get('project_files', []), self.project_dir)
        self.kill_files(project_files)
        batch_files = resolve_filenames(
            module.get('batch_files', []), self.batch_dir)
        self.kill_files(batch_files)
        self.restart_project()

    def restart_project(self):
        if DRY_RUN:
            self.logger.info('Will restart project: %s' % self.project_dir)
            return
        self.logger.info('Restarting project: %s' % self.project_dir)
        # Set modification time to current time.
        os.utime(self.project_dir, None)

    def reset_project(self, confirm=False):
        if not confirm:
            raise iBRAINToolError('Reset action requires confirmation, e.g. '
                                  'you can use --force action')
        self.logger.info('Reseting project: %s' % self.project_dir)
        # Kill folders and files.
        for key in RESET_LIST:
            kill_files = RESET_LIST[key].get('project_files', [])
            self.kill_files(resolve_filenames(kill_files, self.project_dir))
            kill_folders = RESET_LIST[key].get('project_folders', [])
            self.kill_folders(resolve_filenames(
                kill_folders, self.project_dir, filetype='d',
            ))
        self.restart_project()

    def list_batch_dir(self):
        if self.__batch_listing is None:
            print('Listing batch folder. Please wait: ')
            self.__batch_listing = list()
            for filename in os.listdir(self.batch_dir):
                self.__batch_listing.append(
                    os.path.join(self.batch_dir, filename))
                sys.stdout.write('.')
            sys.stdout.write('\n')
            sys.stdout.flush()
        return self.__batch_listing

    def resubmit(self, modulename):
        if modulename == 'batchjobs':
            from os.path import basename
            expr = re.compile('Batch_(\d+_to_\d+)')
            parse_batch = lambda filename: expr.search(basename(filename))\
                                           .group(1)
            output_batches = [parse_batch(filename) for filename
                              in self.list_batch_dir()
                              if fnmatch(basename(filename),
                                         'Batch_*_OUT.mat')]
            result_batches = dict(((parse_batch(filename), filename)
                                  for filename in self.list_batch_dir()
                                  if fnmatch(basename(filename),
                                             'Batch_*.results')))
            print('Found %d job results logs vs. %d .MAT output files' %
                  (len(result_batches), len(output_batches)))
            # Check if every result has a corresponding batch output.
            # If not, consider it to be an error.
            error_results = list()
            for batch_span in result_batches:
                if not batch_span in output_batches:
                    print('Resubmitting incomplete batch: %s' % batch_span)
                    error_results.append(result_batches[batch_span])
            if error_results:
                # Kill found errors
                self.kill_files(error_results)
                # Kill submission flags
                submit_flags = resolve_filenames([
                    'SubmitBatchJobs.submitted',
                    'SubmitBatchJobs.resubmitted',
                    'SubmitBatchJobs.runlimit',
                ], self.project_dir)
                self.kill_files(submit_flags)
        elif modulename in RESUBMIT_MODULES:
            self.resubmit_module(modulename)
            # Project is restarted by previous call.
            return

        # Restart the project
        self.restart_project()

    @staticmethod
    def run(args):
        '''Main entry point'''
        tool = iBRAINTool(args.path.strip(), args.is_multiplate,
                          VERBOSITY_LEVELS[args.verbosity])
        if args.reset:
            tool.reset_project(args.force)
            return
        if args.resubmit:
            tool.resubmit(args.resubmit)
            return
        if args.restart:
            if args.restart != 'project':
                # print(args.restart)
                # if ',' in args.restart:
                #     modules = args.restart.split(',')
                # print(modules)
                # exit()
                tool.restart_module(args.restart)
            else:
                tool.restart_project()
            return
        raise iBRAINToolError('Nothing to do')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='iBRAINTool', description='Utility'
                                     'for simplified handling of iBRAIN '
                                     'project(s)')
    parser.add_argument('--version', action='version', version='%(prog)s v' +
                        __version__)
    parser.add_argument('--test', action='store_true',
                        help='Perform doctests')
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help='Increase logging verbosity '
                        '(-v WARN, -vv INFO, -vvv DEBUG)')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        default=False, help='DRY_RUN mode ("off" by '
                        'default)')
    parser.add_argument('--is-multiplate', action='store_true',
                        default=False, help='Is a multi-plate project?')
    parser.add_argument('-p', '--path', nargs='?', default=os.getcwd(),
                        help='Path to an iBRAIN project to work with')
    parser.add_argument('--force', action='store_true', default=False,
                        help='Force action')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--restart', choices=RESTART_CHOICES, nargs='?',
                       const='project', default='project',
                       help='Restart module or project. This kills .MAT '
                       'measurement files if found any. Use --resubmit '
                       'command if you want to resume as much as possible')
    group.add_argument('--reset', action='store_true', default=False,
                       help='Reset project by killing files and folders of '
                       'any output or result')
    group.add_argument('--resubmit', choices=RESUBMIT_CHOICES,
                       help='Resubmit module, trying to resume based on '
                       'previous results (default: batchjobs)')

    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN = args.dry_run
    if not args.verbosity:
        args.verbosity

    if args.test:
        import doctest
        doctest.testmod()
        exit()

    try:
        iBRAINTool.run(args)
    except iBRAINToolError as error:
        print('Error: %s' % error.message, file=sys.stderr)
