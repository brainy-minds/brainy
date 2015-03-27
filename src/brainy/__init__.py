'''
brainy
======

A nimble workflow managing tool, at the core of iBRAIN functionality. It
allows creation of projects according to the expected framework layout.
It also oversees the execution of the projects and provides monitoring of any
relevant progress of the conducted computation.

@author: Yauhen Yakimovich <yauhen.yakimovich@uzh.ch>,
         Pelkmans lab <https://www.pelkmanslab.org>

@license: The MIT License (MIT)

Copyright (c) 2014 Pelkmans Lab

'''
from brainy.version import __version__, brainy_version


# Mapping command shortcuts to brainy bin scripts.
DUTIES = {
    'brainy-config': {
        'imperatives': [
            'help',
            'init',
            'test',
        ],
        'subjectives': [
            'config',
        ],
        'description': 'Init brainy configuration in ~/.brainy user-path.',
    },
    'brainy-frames': {
        'imperatives': [
            'help',
            'update',
            'install',
            'list',
            'search',
            'apply',
        ],
        'subjectives': [
            'frame',
            'frames',
        ],
        'description': 'Package management system for brainy.',
    },
    'brainy-project': {
        'imperatives': [
            'help',
            'create',
            'restart',
            'run',
            'clean',
            'init',
        ],
        'subjectives': [
            'project',
            'projects',
        ],
        'description': 'Manage brainy projects: create new onces, '
                       'run existing.',
    },
    'brainy-web': {
        'imperatives': [
            'help',
            'serve',
        ],
        'subjectives': [
            'web',
            'ui',
            'http',
        ],
        'description': 'Starts a local web server and opens a GUI in browser.',
        'use_exec': True,
    },
}
