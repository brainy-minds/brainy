'''
brainy.config

Save and load configuration files.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab <https://www.pelkmanslab.org>

@license: The MIT License (MIT). Read a copy of LICENSE distributed with
          this code.

Copyright (c) 2014-2015 Pelkmans Lab
'''
import os
from getpass import getuser
import logging
from brainy.version import brainy_version
from brainy.utils import (merge_dicts, load_yaml, dump_yaml,
                          replace_template_params)

logger = logging.getLogger(__name__)

# A list of config pathnames that are merged (lists that are glued)
# when multiple configs are merged into one.
BRAINY_MERGED_PATHNAMES = [
    # Note that a path name is a list of keys in the nested dict.
    ['brainy', 'pipe_namespaces'],
    ['brainy', 'workflows'],
    ['languages', 'python', 'path'],
    ['languages', 'matlab', 'path'],
]


# User-wide brainy configuration template.
#
# Note that all %(user_home)s are replaced by expanded full path to home
# folder.
BRAINY_USER_CONFIG_TPL = '''# brainy user config
brainy:
  version: '%(brainy_version)s'
  admin_email: 'root@localhost'
  user: '%(brainy_user)s'
  lib_path: '%(user_home)s/.brainy/lib'

  pipe_extension: '.br'

  # A list of prefixes of python class names where brainy looks for pipe
  # and process types. See brainy.pipes.manager.PipesManager.pipe_namespaces
  pipe_namespaces: ['brainy.pipes']

  # A list of paths to multiple possible workflow locations.
  # Each folder in the path has a simple format.
  # It contains folders (name of the folder == name of the workflow)
  # each having multiple .br files (pipes === YAML files with parts of the
  #                                 workflow description)
  workflows: ['%(user_home)s/.brainy/workflows']

  # iBRAIN is a framework_name iBRAIN will look for by default.
  default_framework: 'iBRAIN'

# Which scheduling API to use by default?
scheduling:
  # Possible choices are: {'shellcmd', 'lsf', 'slurm'}
  engine: 'shellcmd'

# Preliminary programming languages. Note that each `path` entry
# for a corresponding language is a setting that brainy prependeds
# to the environment of submitted jobs.
languages:
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


# Default project parameters
project_parameters:
  job_submission_queue: '8:00'
  job_resubmission_queue: '36:00'

''' % {
    'brainy_version': brainy_version,
    'brainy_user': getuser(),
    'user_home': os.path.expanduser('~'),
}

BRAINY_USER_CONFIG_PATH = os.path.expanduser('~/.brainy/config')

BRAINY_USER_PACKAGES_INDEX_PATH_TPL = os.path.expanduser(
    '~/.brainy/%(framework_name)s.packages_index')

# Project specific configuration
BRAINY_PROJECT_CONFIG_TPL = '''# brainy project config
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
    '''
    This function is called at different levels, e.g. by BrainyProject.create()
    (in brainy.project.base)" to drop a YAML file into a project folder.
    '''
    logger.info('Writing config: %s' % config_path)
    if type(value) == dict:
        value = dump_yaml(value)
    with open(config_path, 'w+') as stream:
        stream.write(value)


def load_config(config_path):
    '''
    This function is called at different levels, e.g. by BrainyProject.run
    to load the actual config file(s) and return it as a nested key-value
    dictionary.
    '''
    logger.info('Loading config: %s' % config_path)
    with open(config_path) as template_stream:
        # Replace all %(user_home)s by expanded full path to home folder.
        stream = replace_template_params(template_stream, {
            'user_home': os.path.expanduser('~'),
        })
        return load_yaml(stream.read())


def merge_config(*configs):
    '''
    A brainy-specifics and config aware way to deep-merge nested key-value
    pairs of dictionaries (usually stored as YAML format).

    Important: use this only for loading and don't write back to YAML since
    it will not preserve comments.
    '''
    if len(configs) < 2:
        raise Exception('Two or more configs are expected as arguments.')
    if not all([type(config) == dict for config in configs]):
        raise Exception('Not all configs are dicts.')
    result = dict()
    for config in configs:
        result = merge_dicts(result, config,
                             append_lists=BRAINY_MERGED_PATHNAMES)
    return result


def append_to_list_in_config(yaml_filepath, key_path, value):
    '''
    Load YAML. Find the key or a sub key. It must be a list.
    Append the value the end of the list.
    '''


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
    '''
    This function is called by BrainyProject.run to load from user-wide
    configuraiton, usually ~/.brainy/config
    '''
    if not os.path.exists(BRAINY_USER_CONFIG_PATH):
        logger.error('Missing "%s". Have you forgot `brainy config init` ?' %
                     BRAINY_USER_CONFIG_PATH)
        exit()
    return load_config(BRAINY_USER_CONFIG_PATH)


def write_project_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME,
                         inherit_config={}, override_config={}):
    '''
    Serves the need to produce YAML files. Called by BrainyProject.create()
    '''
    config_path = os.path.join(project_path, config_name)
    if inherit_config or override_config:
        value = load_yaml(BRAINY_PROJECT_CONFIG_TPL)
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
    '''
    Called by BrainyProject.run() to load project specific settings, i.e.
    defined only for the evaluated project and applied to the project workflow.
    '''
    config_path = os.path.join(project_path, config_name)
    return load_config(config_path)


def project_has_config(project_path, config_name=BRAINY_PROJECT_CONFIG_NAME):
    config_path = os.path.join(project_path, config_name)
    return os.path.exists(config_path)


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
        return load_yaml(stream.read())


def load_brainy_config():
    '''
    Merge user-wide config and every framework config.

    This does not include project specific or workflow (pipe specific)
    settings.
    '''
    config = load_user_config()
    # For now we merge only one framework.
    frameworks = [config['brainy']['default_framework']]
    configs = [config]
    for framework in frameworks:
        # Such path formation might change in the future.
        framework_config_path = os.path.expanduser('~/%s/config.yaml' %
                                                   framework)
        logger.info('Merging config: %s' % framework_config_path)
        configs.append(load_config(framework_config_path))
    return merge_config(*configs)
