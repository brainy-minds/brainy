'''
brainy.process on of the central building blocks of brainy.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab <https://www.pelkmanslab.org>

@license: The MIT License (MIT). Read a copy of LICENSE distributed with
          this code.

Copyright (c) 2014-2015 Pelkmans Lab
'''

import os
import re
import logging
import pprint
from datetime import datetime
from pipette.pipes import Process as PipetteProcess
from brainy.flags import FlagManager
from brainy.scheduler import SHORT_QUEUE, NORM_QUEUE
from brainy.errors import (UnknownError, KnownError, TermRunLimitError,
                           check_report_file_for_errors, BrainyProcessError)
from brainy.project.report import BrainyReporter
logger = logging.getLogger(__name__)


PROCESS_STATUS = [
    'submitting',
    'waiting',
    'resubmitted',
    'reseted',
    'failed',
    'completed',
]


def format_code(code, lang='bash'):
    result = ''
    if lang == 'python':
        left_strip_width = None
        for line in code.split('\n'):
            if len(line.strip()) == 0:
                continue
            if left_strip_width is None:
                # Strip only first left.
                left_strip_width = 0
                j = 0
                while j < len(line):
                    if line[j] == ' ':
                        left_strip_width += 1
                        j += 1
                    else:
                        break
            result += line.rstrip()[left_strip_width:] + '\n'
    else:
        for line in code.split('\n'):
            if len(line.strip()) == 0:
                continue
            result += line.strip() + '\n'
    return result


class BrainyProcess(PipetteProcess, FlagManager):

    def __init__(self):
        super(BrainyProcess, self).__init__()
        self.__reports = None
        self.__batch_listing = None
        self._job_report_exp = None
        # List all the relevant process parameters that can be injected into
        # description values. This provides an additional level of
        # parametrization. Also see format_with_params()
        self.format_parameters = [
            'name',
            'step_name',
            # 'plate_path',  # Deprecated
            'project_path',
            'process_path',
            # 'pipes_path', # Deprecated
            'reports_path',
            # 'batch_path',   # Deprecated
            # 'tiff_path',   # Deprecated
            'data_path',
            'images_path',
            'analysis_path',
            # 'postanalysis_path',  # Deprecated
            # 'jpg_path',  # Deprecated
            'job_submission_queue',
            'job_resubmission_queue',
        ]
        self.compiled_params = dict()
        self.report_name_postfix = ''

    @property
    def pipes_manager(self):
        # FIXME: Pass everything to parameters. Make process independent from
        # manager.
        return self.parameters['pipes_manager']

    @property
    def config(self):
        return self.parameters['pipes_manager'].config

    @property
    def scheduler(self):
        return self.parameters['pipes_manager'].scheduler

    @property
    def name(self):
        return self.parameters['name']

    @property
    def step_name(self):
        return self.parameters['step_name']

    @property
    def job_report_exp(self):
        return self.parameters.get(
            'job_report_exp',
            '%s_\d+.job_report' % self.name if self._job_report_exp is None
            else self._job_report_exp,
        )

    @property
    def project_path(self):
        # We don't allow to parametrize project_path for security reasons.
        # See method restrict_to_safe_path() below.
        return self.parameters['pipes_manager'].project_path

    def restrict_to_safe_path(self, pathname):
        '''Restrict every relative pathname to point within the plate path'''
        try:
            safe_path = self.project_path
            if not safe_path.endswith('/'):
                safe_path += '/'
            if '../../' in pathname:
                pathname = pathname.replace('../../', safe_path, 1)
            pathname = pathname.replace('..', '')
            # The actual jailing withing the safe_path.
            assert pathname.startswith(safe_path)
            return pathname
        except Exception as error:
            logger.error('Safe check failed: %s' % pathname)
            logger.exception(error)
            raise error

    @property
    def process_path(self):
        return self.restrict_to_safe_path(self.parameters['process_path'])

    @property
    def reports_path(self):
        reports_path = self.parameters.get(
            'reports_path',
            os.path.join(self.process_path, 'job_reports_of_{name}'),
        )
        reports_path = self.format_with_params('reports_path', reports_path)
        return self.restrict_to_safe_path(reports_path)

    @property
    def data_path(self):
        '''All the shared data of the process are located here.'''
        data_path = self.parameters.get(
            'data_path',
            os.path.join(self.process_path, 'data_of_{name}'),
        )
        data_path = self.format_with_params('data_path', data_path)
        return self.restrict_to_safe_path(data_path)

    @property
    def images_path(self):
        '''All the shared images of the process are located here.'''
        images_path = self.parameters.get(
            'images_path',
            os.path.join(self.process_path, 'images_of_{name}'),
            # os.path.join(self.process_path, 'images'),
        )
        images_path = self.format_with_params('images_path', images_path)
        return self.restrict_to_safe_path(images_path)

    @property
    def analysis_path(self):
        analysis_path = self.parameters.get(
            'analysis_path',
            os.path.join(self.process_path, 'analysis_of_{name}'),
            # os.path.join(self.process_path, 'analysis'),
        )
        analysis_path = self.format_with_params('analysis_path',
                                                analysis_path)
        return self.restrict_to_safe_path(analysis_path)

    @property
    def job_submission_queue(self):
        return self.parameters.get(
            'job_submission_queue',
            SHORT_QUEUE,
        )

    @property
    def job_resubmission_queue(self):
        return self.parameters.get(
            'job_resubmission_queue',
            NORM_QUEUE,
        )

    @property
    def bash_call(self):
        return self.parameters.get(
            'bash_call',
            self.config['languages']['bash']['cmd'],
        )

    @property
    def matlab_call(self):
        return self.parameters.get(
            'matlab_call',
            self.config['languages']['matlab']['cmd'],
        )

    @property
    def python_call(self):
        return self.parameters.get(
            'python_call',
            self.config['languages']['python']['cmd'],
        )

    def get_brainy_lib_path(self, lang):
        '''
        Path entry for a corresponding language is a setting that brainy
        prependeds to the environment of submitted jobs.
        '''
        lang_env_path = [
            os.path.join(self.config['brainy']['lib_path'],
                         lang.lower()),
        ]
        # Extend path with values from config. E.g.
        # ['languges']['matlab']['path'] must be list
        if 'path' in self.config['languages'][lang.lower()]:
            config_lang_path = self.config['languages'][lang.lower()]['path']
            assert type(config_lang_path) == list
            lang_env_path = config_lang_path + lang_env_path
        return lang_env_path

    @property
    def user_bash_path(self):
        user_path = self.parameters.get('user_bash_path',
                                        '{project_path}/lib/bash')
        return self.format_with_params('user_bash_path', user_path)

    @property
    def user_matlab_path(self):
        user_path = self.parameters.get('user_matlab_path',
                                        '{project_path}/lib/matlab')
        return self.format_with_params('user_matlab_path', user_path)

    @property
    def user_python_path(self):
        user_path = self.parameters.get('user_python_path',
                                        '{project_path}/lib/python')
        return self.format_with_params('user_python_path', user_path)

    def get_user_code_path(self, lang='python', valid_folders=None):
        if valid_folders is None:
            valid_folders = list()
        # Brainy path from deployed code.
        brainy_lib_path = self.get_brainy_lib_path(lang)
        valid_folders += brainy_lib_path
        # User path from config.
        property_name = 'user_%s_path' % lang.lower()
        if hasattr(self, property_name):
            value = getattr(self, property_name)
            # If it is not a list then it must be a colon separated string
            if isinstance(value, basestring):
                user_path = value.split(':')
            elif type(user_path) == list:
                user_path = value
            else:
                raise Exception('User path must be either a string or a list.')
            for subfolder in user_path:
                if '~/' in subfolder:
                    subfolder = os.path.expanduser(subfolder)
                folder_path = subfolder
                if not os.path.exists(folder_path):
                    logger.warning('The custom code path does not exist: %s' %
                                   folder_path)
                    continue
                valid_folders.append(folder_path)
        # Pack result as colon separated string
        logger.info('Using custom folder path for %s: %s' %
                    (lang, valid_folders))
        return ':'.join(valid_folders)

    def format_with_params(self, param_name, value):
        '''
        Inject updated values into the code. This applies string.format() DSL
        using self.parameters dictionary as arguments.
        '''
        if param_name not in self.compiled_params:
            logger.debug('Compiling (string substitution) param: %s' %
                         param_name)
            process_params = dict()
            for name in self.format_parameters:
                param_var = '{%s}' % name
                if param_var not in value:
                    # Pick only those values that we really need to compile the
                    # parameter - do string substitution.
                    continue
                process_params[name] = getattr(self, name)
            # Compile by substituting every {variable} with its value.
            try:
                compiled_value = value.format(**process_params)
            except KeyError as error:
                message = ('Failed to compile {%s}. Missing value for key'
                           ' %s in expression: "%s".') % \
                          (param_name, str(error), value)
                message += ' Consider doubling the {{ and }} to print { and }.'
                raise BrainyProcessError(message=message,
                                         message_type='warning')
            self.compiled_params[param_name] = compiled_value
        return self.compiled_params[param_name]

    def _get_flag_prefix(self):
        return os.path.join(self.process_path, self.name)

    def get_job_reports(self):
        if self.__reports is None:
            # Find result files only once.
            reports_regex = re.compile(self.job_report_exp)
            self.__reports = [filename for filename
                              in os.listdir(self.reports_path)
                              if reports_regex.search(filename)]
        return self.__reports

    def list_batch_dir(self):
        # FIXME: Does this function still make sense for listing outputs?
        if self.__batch_listing is None:
            logger.info('Listing batch folder. Please wait.. ')
            self.__batch_listing = list()
            for filename in os.listdir(self.batch_path):
                self.__batch_listing.append(
                    os.path.join(self.batch_path, filename))
            #     sys.stdout.write('.')
            # sys.stdout.write('\n')
            # sys.stdout.flush()
        return self.__batch_listing

    def make_report_filename(self):
        return os.path.join(
            self.reports_path, '%s%s_%s.job_report' %
            (self.name, self.report_name_postfix,
             datetime.now().strftime('%y%m%d%H%M%S')))

    def submit_job(self, shell_command, queue=None, report_file=None,
                   is_resubmitting=False):
        # Differentiate between submission and resubmission parameters.
        if is_resubmitting:
            if not queue:
                queue = self.job_resubmission_queue
        else:
            if not queue:
                queue = self.job_submission_queue
        # Form a unique report file path.
        if not report_file:
            report_file = self.make_report_filename()
        elif not report_file.startswith('/'):
            report_file = os.path.join(self.reports_path, report_file)
        assert os.path.exists(os.path.dirname(report_file))
        return self.scheduler.submit_job(shell_command, queue, report_file)

    def bake_bash_code(self, bash_code):
        return '''%(bash_call)s << BASH_CODE;
export PATH="%(user_path)s:$PATH"
%(bash_code)s
BASH_CODE''' % {
            'bash_call': self.bash_call,
            'bash_code': format_code(bash_code, lang='bash'),
            'user_path': self.get_user_code_path(lang='bash'),
        }

    def submit_bash_job(self, bash_code, queue=None, report_file=None,
                        is_resubmitting=False):
        script = self.bake_bash_code(bash_code)
        return self.submit_job(script, queue, report_file)

    def bake_matlab_code(self, matlab_code):
        return '''%(matlab_call)s << MATLAB_CODE;
path('%(user_path)s', path());
path(getrecpath('%(user_path)s'), path());

%(matlab_code)s
MATLAB_CODE''' % {
            'matlab_call': self.matlab_call,
            'matlab_code': format_code(matlab_code, lang='matlab'),
            'user_path': self.get_user_code_path(lang='matlab'),
        }

    def submit_matlab_job(self, matlab_code, queue=None, report_file=None,
                          is_resubmitting=False):
        script = self.bake_matlab_code(matlab_code)
        return self.submit_job(script, queue, report_file)

    def bake_python_code(self, python_code):
        user_path = str(self.get_user_code_path(
                        lang='python')).split(':')
        assert type(user_path) == list
        return '''%(python_call)s - << PYTHON_CODE;
import sys
sys.path = %(user_path)s + sys.path
%(python_code)s
PYTHON_CODE''' % {
            'python_call': self.python_call,
            'python_code': format_code(python_code, lang='python'),
            'user_path': user_path,
        }

    def submit_python_job(self, python_code, queue=None, report_file=None,
                          is_resubmitting=False):
        script = self.bake_python_code(python_code)
        return self.submit_job(script, queue, report_file)

    @property
    def job_reports_count(self):
        return len(self.get_job_reports())

    def has_job_reports(self):
        return self.job_reports_count > 0

    def working_jobs_count(self, needle=None):
        if needle is None:
            # TODO: make jobs more specific. Process path is too general.
            needle = os.path.dirname(self.reports_path)
        return self.scheduler.count_working_jobs(needle)

    def put_on(self):
        super(BrainyProcess, self).put_on()
        # Create missing process folder path.
        if not os.path.exists(self.process_path):
            os.makedirs(self.process_path)
        # Create missing job reports folder path.
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)
        # Set status to
        self.results['step_status'] = 'submitting'

    def want_to_submit(self):
        if self.is_submitted is False and self.is_resubmitted is False \
                and self.is_complete is False:
            return True
        return False

    def no_work_is_happening(self):
        if (self.is_submitted or self.is_resubmitted) \
                and self.is_complete is False \
                and self.working_jobs_count() == 0 \
                and self.has_job_reports() is False \
                and self.has_runlimit is False:
            return True
        return False

    def still_working(self):
        if (self.is_submitted or self.is_resubmitted) \
                and self.is_complete is False:
            return self.has_job_reports() is False \
                and self.working_jobs_count() > 0
        return False

    def has_data(self):
        '''
        Override this method to implement step specific data existence and
        integrity checks.
        '''
        # raise NotImplemented('Missing implementation for has_data() method.')
        return True

    def finished_work_but_has_no_data(self):
        if (self.is_submitted or self.is_resubmitted) \
                and self.is_complete is False \
                and self.has_runlimit() is False:
            # Independent of the fact if we have reports or not, not having any
            # data or jobs running is good enough to attempt resubmission.
            return bool(self.has_data()) is False
        return False

    def report(self, message, warning=''):
        if warning:
            logger.warn(warning)
            BrainyReporter.append_warning(warning)
        logger.info('%(step_name)s: %(message)s %(warning)s' % {
            'step_name': self.step_name,
            'message': message,
            'warning': warning,
        })
        BrainyReporter.append_message(message)

    def has_runlimit(self):
        return os.path.exists(self.get_flag('runlimit'))

    def remove_job_report_file(self, report_filepath):
        '''Remove file from the disk as well as from the cache.'''
        # Clean cache.
        report_filename = os.path.basename(report_filepath)
        if report_filename in self.__reports:
            item_index = self.__reports.index(report_filename)
            del self.__reports[item_index]
        # Remove from disk.
        os.unlink(report_filepath)

    def check_logs_for_errors(self):
        for report_filename in list(self.get_job_reports()):
            # print report_filename
            report_filepath = os.path.join(self.reports_path, report_filename)
            try:
                check_report_file_for_errors(report_filepath)
            except TermRunLimitError as error:
                if self.has_runlimit():
                    message = 'Job %s timed out too many times.' % \
                        report_filename
                    raise BrainyProcessError(
                        message=message.strip(),
                        message_type='warning',
                        output=error.details,
                        job_report=report_filepath,
                    )
                else:
                    BrainyReporter.append_known_error(
                        'Job has exceeded runlimit, resetting job and placing '
                        'timeout flag file')
                    self.set_flag('runlimit')
            except KnownError as error:
                self.reset_resubmitted()
                message = 'Resetting ".(re)submitted" and ".runlimit" flags'\
                    ' and removing job report.'
                # Modifies self.__reports
                self.remove_job_report_file(report_filepath)
                raise BrainyProcessError(
                    message=message,
                    message_type='warning',
                    output=str(error) + error.details,
                    error_type=error.type,
                )
            except UnknownError as error:
                message = 'Unknown error found in job report file %s' % \
                    report_filename
                raise BrainyProcessError(
                    message=message,
                    message_type='warning',
                    output=str(error) + error.details,
                )
        # Finally, no errors were found.

    def resubmit(self):
        self.set_flag('runlimit')

    def check_for_missed_errors(self):
        '''
        "Check for errors" might have failed to detect the error, so we still
        need to make sure that our data was generated correctly.
        '''
        if not self.has_data():
            report_filepath = None
            if self.has_job_reports():
                # Pick latest report
                reports = self.get_job_reports()
                if len(reports) > 0:
                    report_filename = reports[0]
                    report_filepath = os.path.join(self.reports_path,
                                                   report_filename)
            if self.has_runlimit():
                message = 'We reached a limit of retry attempts, but data are'\
                    + ' missing possibly due to some undetected errors. Pleas'\
                    + 'e inspect the corresponding log files.'
                raise BrainyProcessError(message=message,
                                         message_type='warning',
                                         job_report=report_filepath)
            raise BrainyProcessError(message='Data are missing possibly due to'
                                     ' some undetected errors. Please inspect '
                                     'the corresponding log files.',
                                     message_type='warning',
                                     job_report=report_filepath)

    def run(self):
        logger.info('running process <%s> with the following parameters:' %
                    self.name)
        logger.info(pprint.pformat(self.parameters))
        # print self.get_job_reports()
        # print self.working_jobs_count()
        # Skip if ".complete" flag was found.
        if self.is_complete:
            self.results['step_status'] = 'completed'
        # Step is incomplete. Do we want to submit?
        elif self.want_to_submit():
            if self.working_jobs_count() > 0:
                logger.warn('Some jobs are still running, but we are '
                            'submitting everything a new!')
            self.submit()
        # Submitted but no work has started yet?
        elif self.no_work_is_happening():
            self.report('resetting', warning='No work is happening')
            self.reset_submitted()
        # Waiting.
        elif self.still_working():
            self.report('waiting')
        # Resubmit if no data output but job results found.
        elif self.finished_work_but_has_no_data():
            # Hint: check if has_data() works correctly!
            self.resubmit()
        # Check for known errors if both data output and job results are
        # present.
        else:
            logger.info('Checking logs for errors. Setting process state to '
                        'completed if none found.')
            self.check_logs_for_errors()
            self.check_for_missed_errors()
            # At this point we have detected no errors and the data test
            # has passed -> mark process as 'completed'.
            self.results['step_status'] = 'completed'
            self.set_flag('complete')

    def reduce(self):
        if self.results['step_status'] == 'completed':
            logger.info('Step {%s} was completed.' % self.step_name)
            BrainyReporter.append_message('complete', status='complete')
