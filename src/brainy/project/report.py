import os
import yaml
from datetime import datetime
from brainy.log import json_handler
import logging
logger = logging.getLogger(__name__)

# This is a global namespace variable containing a DOM-like structure of
# project report. It is mainly modified during `brainy run project` call.
report_data = {}


def get_now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def start_report():
    report_data['started_at'] = datetime.now()


def finalize_report():
    '''Produce final report structure as JSON'''
    report_data['finished_at'] = datetime.now()
    report_data['log'] = json_handler.houtput.root  # points to dictionary


def save_report(report_filepath):
    reports_folder = os.path.dirname(report_filepath)
    if not os.path.exists(reports_folder):
        logger.info('Creating missing reports folder: %s' % reports_folder)
        os.makedirs(reports_folder)
    now_str = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    report_filepath = '%s-report-%s.yaml' % (report_filepath, now_str)
    with open(report_filepath, 'w+') as reportfile:
        reportfile.write(yaml.dump(report_data, default_flow_style=False))
