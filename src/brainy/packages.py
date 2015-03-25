'''
Manages frameworks and frames (packages).

NB Yes, it is totally inspired by `brew`.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2015 Pelkmans Lab
'''
import os
import sys
from sh import git
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import brainy.config
import logging


logger = logging.getLogger(__name__)
user_config = brainy.config.load_user_config()


class Frames(object):
    '''
    A frame is a package.
    '''

    def __init__(self, location, framework_location=None):
        # Framework location, e.g. ~/iBRAIN
        self.location = location
        self._packages = None

    @property
    def cache_location(self):
        return os.path.join(self.location, '.frames')

    @property
    def package_list_path(self):
        '''A YAML list of installed packages'''
        return os.path.join(self.cache_location, '.packages')

    @property
    def packages(self):
        '''
        A proxy around YAML list of installed packages.
        Simplifies any direct YAML I/O.
        Returns a list of dicts.
        '''
        if self._packages is None:
            logger.info('Loading list of installed packaged: %s' %
                        self.package_list_path)
            with open(self.package_list_path) as stream:
                self._packages = yaml.load(stream, Loader=Loader)
        return self._packages

    @packages.setter
    def packages(self, value):
        assert type(value) == dict
        self._packages = value
        yaml_list = yaml.dump(value, default_flow_style=True)
        logging.info('Saving list of installed packaged: %s' %
                     self.package_list_path)
        with open(self.package_list_path, 'w+') as output:
            output.write(yaml_list)

    def init(self):
        if not os.path.exists(self.location):
            logger.info('Initializing framework folders and caches at: %s' %
                        self.location)
            os.makedirs(self.cache_location)
            logger.info('Creating empty list of installed packages: %s' %
                        self.location)
            self.packages = list()

    def update_index(self, framework='iBRAIN'):
        '''
        Brainy user configuration provides an URL to get
        project index.
        '''
        # TODO replace this hardcoded index by URL download
        packages_index = '''
# iBRAIN Framework
index version: 1
packages:
    -
        name: 'iBRAIN'

        # Default value 'master'
        # version: 'master'

        # Namespace of the package is parsed from URL if possible.
        # In case of the GITHUB workflow it corresponds to the project owner.
        # namespace: 'pelkmanslab'
        # url: 'https://github.com/pelkmanslab/iBRAIN'

        # Also see https://github.com/pelkmanslab/iBRAIN/blob/master/README.md
        # on how to get access to pelkmanslab_github

        # If URL does ends with .tar.gz or .zip then git is assumed.
        url: 'pelkmanslab_github:pelkmanslab/iBRAIN'

        # More keys: homepage, sha1, md5

    -
        name: iBRAINModules
        url: 'pelkmanslab_github:pelkmanslab/iBRAINModules'коменте

'''     # Write index to ~/.brainy/<framework>.packages_index
        brainy.config.update_packages_index(framework,
                                            yaml_data=packages_index)

    def install_frame(self, frame):
        '''Implemented by package.'''
        logger.info('Downloading (%s) %s <- %s', frame.access_method,
                    frame.name, frame.url)
        package_frame_path = ''


class Frame(object):
    '''
    Describes how to install the frame. Place it inside framework.
    Note: more less equivalent to `Formula` in `brew`.
    '''

    def __init__(self, name, url='', namespace='', version='',
                 homepage='', sha1='', md5='', access_method='git'):
        self.name = name
        self.url = url
        self.namespace = namespace
        self.version = version
        self.homepage = homepage
        self.sha1 = sha1
        self.md5 = md5
        self.access_method = access_method

    def download(self, frames):
        if self.access_method == 'git':
            res = git.clone(self.url, os.path.join(
                            frames.cache_location, self.name))
            if not res.exit_code == 0:
                riase Exception('Failed to clone %s from: %s' %
                                (self.name, self.url))
        else:
            raise Exception('Unknown access method: %s' % self.access_method)

    def parse_url(self):
        '''Guess empty fields from URL or fail.'''


    def as_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'namespace': self.namespace,
        }

