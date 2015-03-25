'''
brainy.config

Save and load configuration files.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2014 Pelkmans Lab
'''
import os
import re
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from getpass import getuser
import logging
logger = logging.getLogger(__name__)
from brainy.version import brainy_version
from brainy.utils import merge_dicts


# User-wide (global) configuration
BRAINY_USER_CONFIG_TPL = '''
# brainy user config
brainy:
    version: '%(brainy_version)s'
    user: '%(brainy_user)s'
    lib_path: '%(brainy_lib_path)s'
    pipe_extension: '.br'
    admin_email: 'root@localhost'
    default_framework: 'iBRAIN'


# Which scheduling API to use by default?
scheduling:
    # Possible choices are: {'shellcmd', 'lsf', 'slurm'}
    engine: 'shellcmd'

# Preliminary tools and programming languages
tools:
    python:
        cmd: '/usr/bin/env python2.7'
    matlab:
        cmd: '/usr/bin/env matlab -singleCompThread -nodisplay -nojvm'
    ruby:
        cmd: '/usr/bin/env ruby'
    node:
        cmd: '/usr/bin/env node'
    bash:
        cmd: '/bin/bash'


# Integrated application
apps:
    CellProfiler2:
        path: '%(cellprofiler2_path)s'

# Default project parameters
project_parameters:
    job_submission_queue: '8:00'
    job_resubmission_queue: '36:00'

''' % {
    'brainy_version': brainy_version,
    'brainy_user': getuser(),
    'cellprofiler2_path': os.path.expanduser(
        '~/iBRAINFramework/tools/CellProfiler2'),
    'brainy_lib_path': os.path.join(
        os.path.dirname(__file__),
        'lib',
    ),
}
BRAINY_USER_CONFIG_PATH = os.path.expanduser('~/.brainy/config')

BRAINY_USER_NAMESPACES_PATH = os.path.expanduser('~/.brainy/namespaces')
NAMESPACE_REGEXP = r'\S*'
# Cache
NAMESPACES = None

BRAINY_USER_PACKAGES_INDEX_PATH_TPL = os.path.expanduser(
    '~/.brainy/%(framework_name)s.packages_index')

# Project specific configuration
BRAINY_PROJECT_CONFIG_TPL = '''
# brainy project config
brainy:
    version: '%(brainy_version)s'

# Parameters below will affect the whole project. In particular, that defines
# how jobs in every step of each pipe will be submitted, which folder names
# and locations are used, etc.

# Uncomment these section to use parallel submission engines once your project
# is deployed onto a cluster.
#
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
    if type(value) == dict:
            value = yaml.dump(value, default_flow_style=True)
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
        os.makedirs(user_brainy_path)
    if os.path.exists(user_config_path):
        logger.warn('Abort. Configuration file already exists: %s' %
                    user_config_path)
        return
    write_config(user_config_path, BRAINY_USER_CONFIG_TPL)


def load_user_config():
    return load_config(BRAINY_USER_CONFIG_PATH)


def write_project_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME,
                         inherit_config={}, override_config={}):
    config_path = os.path.join(project_path, config_name)
    if inherit_config or override_config:
        value = yaml.load(BRAINY_PROJECT_CONFIG_TPL)
        if inherit_config:
            value = merge_dicts(inherit_config, value)
        if override_config:
            value = merge_dicts(value, override_config)
    else:
        value = BRAINY_PROJECT_CONFIG_TPL
    write_config(
        config_path=config_path,
        value=value,
    )


def load_project_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    return load_config(config_path)


def project_has_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    return os.path.exists(config_path)


def load_process_namespaces():
    '''
    Every time we instantiate Pipes and Processes according to the type
    defined in YAML files, brainy will look up over the python PATH for
    classes which fully-qualified class datatype is restricted by the list
    of namespaces returned by this config function.

    See brainy.pipes.base. and pipette.Pipe.find_process_class()

    Each package if it contains any Pipes or Processes will append
    its own namespace to text file usually located: ~/.brainy/namespaces
    '''
    global NAMESPACES
    # Cache
    if NAMESPACES is None:
        NAMESPACES = [line for line in
                      open(BRAINY_USER_NAMESPACES_PATH).readlines()
                      if len(line.strip()) > 0]
        for namespace in NAMESPACES:
            if not NAMESPACE_REGEXP.match(namespace):
                raise Exception('Wrong namespace: %s' % namespace)
    return NAMESPACES


def update_packages_index(framework_name, yaml_data):
    '''Write packages index to disk'''
    index_filepath = BRAINY_USER_PACKAGES_INDEX_PATH_TPL % {
        'framework_name': framework_name,
    }
    with open(index_filepath, 'w+') as packages_index:
        packages_index.write(yaml_data)


def load_packages_index(framework_name):
    index_filepath = BRAINY_USER_PACKAGES_INDEX_PATH_TPL % {
        'framework_name': framework_name,
    }
    with open(index_filepath) as stream:
        return yaml.load(stream, Loader=Loader)
