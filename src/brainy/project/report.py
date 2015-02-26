import os
import yaml
import shutil
from glob import glob
from datetime import datetime
from brainy.log import json_handler
import logging
logger = logging.getLogger(__name__)

# This is a global namespace variable containing a DOM-like structure of
# project report. It is mainly modified during `brainy run project` call.
report_data = {}

UI_WEB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.dirname(__file__)))),
    'ui', 'web')


class BrainyReporter(object):

    @classmethod
    def get_now_str(cls):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def start_report(cls):
        report_data['started_at'] = cls.get_now_str()

    @classmethod
    def finalize_report(cls):
        '''Produce final report structure as JSON'''
        report_data['finished_at'] = cls.get_now_str()
        report_data['log'] = json_handler.houtput.root  # points to dictionary

    @classmethod
    def save_report(cls, report_filepath):
        reports_folder = os.path.dirname(report_filepath)
        if not os.path.exists(reports_folder):
            logger.info('Creating missing reports folder: %s' % reports_folder)
            os.makedirs(reports_folder)
        now_str = datetime.now().strftime('%Y_%m_%d_%H%M%S')
        # Output a human readable YAML file.
        yaml_report_filepath = '%s-report-%s.yaml' % (report_filepath, now_str)
        with open(yaml_report_filepath, 'w+') as yaml_reportfile:
            yaml_reportfile.write(yaml.dump(report_data,
                                  default_flow_style=False))

    @classmethod
    def update_or_generate_static_html(cls, reports_folder_path):
        '''
        Put a copy of static html to browse project reports inside
        'reports/html'.
        '''
        # logger.info('web ui path: %s' % UI_WEB_PATH)
        html_path = os.path.join(reports_folder_path, 'html')
        if not os.path.exists(html_path):
            logger.info('Creating static html to browse reports.')
            # os.makedirs(html_path)
            shutil.copytree(os.path.join(UI_WEB_PATH, 'assets'),
                            os.path.join(html_path, 'assets'))
            shutil.copy(os.path.join(UI_WEB_PATH, 'index.html'),
                        os.path.join(html_path, 'index.html'))
        else:
            logger.info('Updating static html to browse reports.')
        # Generated/update reports.json
        report_list = glob(os.path.join(reports_folder_path,
                           '*-report-*.yaml'))
        report_list = sorted(report_list, reverse=True)
        reports = {
            'modified_at': cls.get_now_str(),
            'reports_list': report_list,
        }
        with open(os.path.join(html_path, 'reports.yaml'), 'w+') \
                as reportsfile:
            reportsfile.write(yaml.dump(reports,
                              default_flow_style=False))

    @classmethod
    def get_current_report_pipe(cls):
        if 'pipes' not in report_data['project']:
            raise Exception('KeyError "pipes". Report data was not properly '
                            'initialized.')
        pipe_index = len(report_data['project']['pipes']) - 1
        if pipe_index < 0:
            raise Exception('Failed to find current pipe. '
                            'Please append a pipe first.')
        return report_data['project']['pipes'][pipe_index]

    @classmethod
    def append_report_pipe(cls, name, **extra):
        pipe = {
            'name': name,
            'processes': [],
        }
        pipe.update(extra)
        if 'pipes' not in report_data['project']:
            report_data['project']['pipes'] = []
        report_data['project']['pipes'].append(pipe)

    @classmethod
    def append_report_process(cls, name, **extra):
        process = {
            'name': name,
        }
        process.update(extra)
        cls.get_current_report_pipe()['processes'].append(process)

    @classmethod
    def get_current_report_step(cls):
        pipe = cls.get_current_report_pipe()
        process_index = len(pipe['processes']) - 1
        if process_index < 0:
            raise Exception('Failed to find current process. '
                            'Please append a process first.')
        return pipe['processes'][process_index]

    @classmethod
    def append_message(cls, message, message_type='info', **kwds):
        process = cls.get_current_report_step()
        if 'messages' not in process:
            process['messages'] = []
        message = {
            'message': message,
            'type': message_type,
        }
        message.update(kwds)
        process['messages'].append(message)

    @classmethod
    def append_warning(cls, message, **kwds):
        '''Unknown error is fatal and should break any further progress'''
        cls.append_message(message, message_type='warning', **kwds)

    @classmethod
    def append_unknown_error(cls, message, **kwds):
        '''Unknown error is fatal and should break any further progress'''
        cls.append_message(message, message_type='unknown_error', **kwds)

    @classmethod
    def append_known_error(cls, message, **kwds):
        '''Known error is typical and causes a series of retries'''
        cls.append_message(message, message_type='known_error', **kwds)
