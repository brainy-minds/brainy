# -*- coding: utf-8 -*-
'''
Manages frameworks and frames (packages).

NB Yes, it is totally inspired by `brew`.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans Lab  <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2015 Pelkmans Lab
'''
import os
from sh import git
import shutil
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import brainy.config
import logging


logger = logging.getLogger(__name__)
user_config = brainy.config.load_user_config()


def parse_frame(frame):
    '''Init with defaults. Guess empty fields from URL or fail.'''
    result = dict()
    result.update(frame)
    result['version'] = frame.get('version', 'master')
    result['access_method'] = frame.get('access_method', 'git')
    return result


class FramesError(Exception):
    '''High-level brainy frames error. Can be handled and reported.'''


class Frames(object):
    '''
    A frame is a package. Frames take care of frameworks installations
    (like iBRAIN) into user space.
    '''

    def __init__(self, framework, location):
        '''
        location is Framework location, e.g. ~/iBRAIN
        '''
        self.framework = framework
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
            if not os.path.exists(self.package_list_path):
                self._packages = list()
                return self._packages
            logger.info('Loading list of installed packages: %s' %
                        self.package_list_path)
            with open(self.package_list_path) as stream:
                self._packages = yaml.load(stream, Loader=Loader)
        return self._packages

    @packages.setter
    def packages(self, value):
        assert type(value) == list
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

    def update_index(self):
        '''
        Brainy user configuration provides an URL to get
        project index.

        A value of framework can be `iBRAIN`.
        '''
        # TODO replace this hardcoded index by URL download
        packages_index = '''
# iBRAIN Framework
index version: 1
packages:
    -
        name: 'iBRAIN'

        # Default value 'master'
        version: 'master'

        # Namespace of the package is parsed from URL if possible.
        # In case of the GITHUB workflow it corresponds to the project owner.
        namespace: 'pelkmanslab'

        # Also see https://github.com/pelkmanslab/iBRAIN/blob/master/README.md
        # on how to get access to pelkmanslab_github

        # If URL does ends with .tar.gz or .zip then git is assumed.
        # url: 'https://github.com/pelkmanslab/iBRAIN'
        url: 'pelkmanslab_github:pelkmanslab/iBRAIN'

        # More keys: homepage, sha1, md5

    -
        name: iBRAINModules
        url: 'pelkmanslab_github:pelkmanslab/iBRAINModules'

'''
        # Write index to ~/.brainy/<framework>.packages_index
        brainy.config.update_packages_index(self.framework,
                                            yaml_data=packages_index)

    def find_frames_in_index(self, name, partial_match=True):
        packages_index = brainy.config.load_packages_index(self.framework)
        found = list()
        for frame in packages_index['packages']:
            # Put in the default values.
            frame = parse_frame(frame)
            # Match.
            name_is_a_match = name in frame['name'] if partial_match \
                else name == frame['name']
            if name_is_a_match:
                logger.info('Found frame: %s' % frame['name'])
                found.append(frame)
        return found

    def get_formula(self, formula_path):
        if not os.path.exists(formula_path):
            raise FramesError('Missing formula (%s) in the package!' %
                              formula_path)
        try:
            # Attempt to execute package frame with class code.
            script_globals = {}
            script_locals = {}
            execfile(formula_path, script_globals   , script_locals)
            # We expect it to instantiate formula object and define it as
            # formula variable.
            if 'formula' not in script_locals:
                FramesError('Package does not define a formula (%s)!' %
                            formula_path)
            return script_locals['formula']
        except SystemExit:
            logger.error('Got SystemExit error')
            raise FramesError('Failed to execute frame installation formula.')

    def download_frame(self, frame, package_path):
        logger.info('Downloading (%s) %s <- %s', frame['access_method'],
                    frame['name'], frame['url'])
        if frame['access_method'].lower() == 'git':
            res = git.clone(frame['url'], package_path)
            if res.exit_code != 0:
                raise FramesError('Git clone failed: %s' % frame['url'])
        else:
            raise FramesError('Unknown access method: %s' %
                              frame['access_method'])

    def apply_formula(self, formula_path, frame):
        formula = self.get_formula(formula_path)

        # Compare with frame information.
        if frame:
            # Checked that formula version and name are correct.
            assert frame['name'] == formula.name
            # TODO: proper version comparison
            # assert frame.version >= formula.version

        # Install the frame from formula.
        formula.install(frames=self)
        return formula

    def install_frame(self, frame, force_reinstall):
        '''Download package and run frame installation formula.'''
        package_path = os.path.join(self.cache_location, frame['name'])
        if os.path.exists(package_path):
            if force_reinstall:
                logger.warn('Purging package from cache: %s' % package_path)
                shutil.rmtree(package_path)
            else:
                raise FramesError('Package is already installed: %s ' %
                                  package_path + ' (maybe --force ?)')
        # Download package.
        self.download_frame(frame, package_path)
        assert os.path.exists(package_path)
        # Get its formula.
        formula_path = os.path.join(package_path, frame['name'] + '_frame.py')
        formula = self.apply_formula(formula_path, frame)

        # Finally save it into list of installed packages.
        self.packages = self.packages + [frame]

        # Done.
        logger.info(('Package "%s" version "%s" was successfully '
                     'installed into: %s') %
                    (formula.name, formula.version, package_path))


class FrameFormula(object):
    '''
    Describes how to install the frame. Place it inside framework.
    Note: more less equivalent to `Formula` in `brew`.

    Effectively a frame is just a piece of python code kept in each packaged.
    After downloading the package brainy frames try to execute this code and
    let it cook the rest of installation.

    Frames object is passed into the routine with information like location of
    the framework.

    Each derived object is called like: `FooFrame` where foo is a name of the
    package.
    '''

    def __init__(self, name, url, namespace='', version='',
                 homepage='', sha1='', md5='', access_method='git'):
        self.name = name
        self.url = url
        self.namespace = namespace
        self.version = version
        self.homepage = homepage
        self.sha1 = sha1
        self.md5 = md5
        self.access_method = access_method

    def as_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'namespace': self.namespace,
            'version': self.version,
            'homepage': self.homepage,
            'sha1': self.sha1,
            'md5': self.md5,
            'access_method': self.access_method,
        }

    def install(self, frames):
        '''Implement it in derived classes of package formulas.'''
