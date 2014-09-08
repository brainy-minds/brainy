'''
brainy.config

Save and load configuration files.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2014 Pelkmans Lab
'''
import os
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from getpass import getuser
import logging
logger = logging.getLogger(__name__)
from brainy.version import brainy_version


# User-wide (global) configuration
BRAINY_USER_CONFIG_TPL = '''
# brainy user config
brainy_version = '%(brainy_version)s'
brainy_user = '%(brainy_user)s'
admin_email = 'root@localhost'

# Which scheduling API to use by default?
scheduling
    # Possible choices are: {'shell_cmd', 'lsf', 'slurm'}
    engine: 'shell_cmd'

# Preliminary tools and programming languages
tools:
    python:
        cmd: '/usr/bin/env python2.7'
    matlab:
        cmd: '/usr/bin/env matlab -singleCompThread -nodisplay -nojvm'
    ruby:
        cmd: '/usr/bin/env ruby'


# Integrated application
apps:
    CellProfiler2:
        path: '%(cellprofiler2_path)s'

# Default project parameters
project_parameters
    job_submission_queue: '8:00'
    job_resubmission_queue: '36:00'

''' % {
    'brainy_version': brainy_version,
    'brainy_user': getuser(),
    'cellprofiler2_path': os.path.expanduser('~/CellProfiler2'),
}
BRAINY_USER_CONFIG_PATH = os.path.expanduser('~/.brainy/config')


# Project specific configuration
BRAINY_PROJECT_CONFIG_TPL = '''
# brainy project config
brainy_version = '%(brainy_version)s'

# Parameters below will affect the whole project. In particular, that defines
# how jobs in every step of each pipe will be submitted, which folders names
# and locations are used, etc.

# Uncomment this once deployed
# scheduling
#     engine: 'lsf'

project_parameters:
    # job_submission_queue: '8:00'
    # job_resubmission_queue: '36:00'
    batch_path: 'data_of_{name}'
    tiff_path: 'images_of_{name}'

''' % {
    'brainy_version': brainy_version,
}
BRAINY_PROJECT_CONFIG_NAME = '.brainy'


def write_config(config_path, value):
    logger.info('Writing config: %s' % config_path)
    with open(config_path, 'w+') as stream:
        stream.write(value)


def load_config(config_path):
    logger.info('Loading config: %s' % config_path)
    with open(config_path) as stream:
        return yaml.load(stream, Loader=Loader)


def write_user_config(user_config_path=BRAINY_USER_CONFIG_PATH):
    '''Write global config into '.brainy' folder inside user's home.'''
    user_brainy_path = os.path.dirname(user_config_path)
    if not os.path.exists(user_brainy_path):
        logger.info('Creating a missing user brainy folder: %s' %
                    user_brainy_path)
    if os.path.exists(user_config_path):
        logger.warn('Abort. Configuration file already exists: %s' %
                    user_config_path)
        return
    write_config(user_config_path, BRAINY_USER_CONFIG_TPL)


def load_user_config():
    return load_config(BRAINY_USER_CONFIG_PATH)


def write_project_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    write_config(
        config_path=config_path,
        value=BRAINY_PROJECT_CONFIG_TPL,
    )


def load_project_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    return load_config(config_path)


def project_has_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    return os.path.exists(config_path)
