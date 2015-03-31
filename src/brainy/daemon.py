# -*- coding: utf-8 -*-
'''
The daemon of brainy. Runs in the background to oversee projects 😈


@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT). Read a copy of LICENSE distributed with
          this code.

Copyright (c) 2014-2015 Pelkmans Lab
'''
import os
import time
import logging
import ConfigParser
from brainy.project.manager import ProjectManager

logger = logging.getLogger(__name__)

# FIXME: Maybe use brainy.config.BRAINY_USER_CONFIG_PATH?
BRAINY_USER_PATH = os.path.expanduser('~/.brainy')


class BrainyApp(object):
    '''
    Bare-bones app that can be wrapped to become a daemon. See BrainyDaemonApp
    '''

    def __init__(self):
        project_list_path = os.path.join(BRAINY_USER_PATH, 'project_list.yaml')
        self.project_manager = ProjectManager(project_list_path)

    def step(self):
        '''A single step of actual work, done by daemon'''
        self.project_manager.build_projects()
        self.project_manager.run_projects()


class BrainyDaemonApp(BrainyApp):
    '''
    If this app is put into a daemon context (daemoncxt) it will
    become a daemon 😈!

    To understand implementation details see DaemonRunner from
    daemoncxt.runner in https://github.com/ewiger/daemoncxt
    '''

    def __init__(self, name, config_vars, debug=True):
        self.name = name
        self.debug = debug
        self.config_name = config_vars.get('config_name')
        self.brainy_user_path = config_vars.get('brainy_user_path')
        self.config = ConfigParser.ConfigParser(defaults=config_vars)
        self.init_config()
        # Inherit wrapped behavior.
        super(BrainyDaemonApp, self).__init__()

    def init_config(self):
        # Start with building some defaults.
        # Init/set application options.
        self.config.add_section('app')
        self.config.set('app', 'log_path',
                        '%(brainy_user_path)s/logs')
        self.config.set('app', 'logging_config_path',
                        '%(brainy_user_path)s/daemon_logging.conf')
        # Init/set daemon options.
        self.config.add_section('daemon')
        self.config.set('daemon', 'stdin_path', '/dev/null')
        self.config.set('daemon', 'stdout_path',
                        '/dev/tty' if self.debug else '/dev/null')
        self.config.set('daemon', 'stderr_path',
                        '/dev/tty' if self.debug else '/dev/null')
        self.config.set('daemon', 'pidfile_path',
                        '%(brainy_user_path)s/' + self.name + '.pid')
        self.config.set('daemon', 'pidfile_timeout', '5')
        self.config.set('daemon', 'sleeping_pause', '10')

    def load_config_file(self, config_name, config_dir):
        '''
        Load configuration from supplied filename. By default configuration
        directory is set to point to '~/.brainy/daemon.conf'
        '''
        config_path = os.path.join(config_dir, config_name)
        if os.path.exists(config_path):
            logger.info('Loading %s' % config_path)
            self.config.read(config_path)

    def load_config(self, config_dir, config_name=None):
        '''Load more configuration from default locations'''
        if config_name is None:
            config_name = self.config_name
        # Load defaults from config dir, i.e. ~/.brainy.
        self.load_config_file(config_name, config_dir)
        # Override with user config.
        # self.load_config_file(config_name, USER_HOME_DIR)

    def validate_config(self):
        '''(Optional) validate config for arguments'''
        # Assert configuration for correctness.
        assert self.config.has_section('app')
        assert os.path.exists(self.config.get('app', 'log_path'))
        assert os.path.exists(self.config.get('app', 'logging_config_path'))

    @property
    def state_path(self):
        if self.__state_path is None:
            # Try to get configuration option.
            self.__state_path = self.config.get('app', 'statepath')
            if not os.path.exists(self.__state_path):
                logger.warn('Creating a missing dir: %s' % self.__state_path)
                os.makedirs(self.__state_path)
        return self.__state_path

    @property
    def stdin_path(self):
        '''Part of DaemonRunner protocol'''
        return self.config.get('daemon', 'stdin_path')

    @property
    def stdout_path(self):
        '''Part of DaemonRunner protocol'''
        return self.config.get('daemon', 'stdout_path')

    @property
    def stderr_path(self):
        '''Part of DaemonRunner protocol'''
        return self.config.get('daemon', 'stderr_path')

    @property
    def pidfile_path(self):
        '''Part of DaemonRunner protocol'''
        return self.config.get('daemon', 'pidfile_path')

    @property
    def pidfile_timeout(self):
        '''Part of DaemonRunner protocol'''
        return self.config.getint('daemon', 'pidfile_timeout')

    def run(self):
        sleeping_pause = self.config.getint('daemon', 'sleeping_pause')
        while True:
            self.step()
            # Sleep x seconds.
            logger.info('Sleeping for %d (sec)..' % sleeping_pause)
            time.sleep(sleeping_pause)


def get_daemon_app(app_name='brainy-daemon', config_vars={},
                   only_defaults=False, **kwds):
    if 'config_name' not in config_vars:
        config_vars['config_name'] = 'daemon.conf'
    if 'brainy_user_path' not in config_vars:
        config_vars['brainy_user_path'] = BRAINY_USER_PATH
    daemon_app = BrainyDaemonApp(app_name, config_vars, **kwds)
    if only_defaults:
        return daemon_app
    # Load configs from ~/.brainy
    daemon_app.load_config(config_dir=BRAINY_USER_PATH)
    # daemon_app.validate_config()
    return daemon_app


def init_daemon_config():
    daemon_app = get_daemon_app()
    # Write config into '~/.brainy/daemon.conf'
    config_path = os.path.join(BRAINY_USER_PATH, daemon_app.config_name)
    logger.info('Writing daemon config: %s' % config_path)
    with open(config_path, 'wb') as configfile:
        daemon_app.config.write(configfile)
