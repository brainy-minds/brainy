#!/usr/bin/env python
import os.path
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


def get_version():
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.append(src_path)
    from brainy.version import brainy_version
    return brainy_version


setup(
    name='brainy',
    version=get_version(),
    description='The nimble workflow managing tool which is a part of iBRAIN '
                'framework for scientific computation primarily applied for '
                'BigData analysis in context of HPC and HTS',
    long_description=readme(),
    author='Yauhen Yakimovich',
    author_email='eugeny.yakimovitch@gmail.com',
    url='https://github.com/pelkmanslab/iBRAIN',
    license='MIT',
    scripts=['brainy'],
    packages=[
        'brainy',
        'brainy.apps',
        'brainy.pipes',
        'brainy.process',
        'brainy.scheduler',
        'brainy.workflows',
    ],
    package_dir = {'':'src'},
    package_data={
        '': ['*.html', '*.svg', '*.js'],
    },
    include_package_data=True,
    download_url='https://github.com/pelkmanslab/iBRAIN/tarball/master',
    install_requires=[
        'pipette~=0.1.2',
        'tree_output~=0.1.2',
    ],
    classifiers=[
        'Topic :: System :: Distributed Computing',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: System :: Emulators',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Programming Language :: Unix Shell',
        'Programming Language :: Ruby',
        'Programming Language :: Java',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    tests_require=['nose>=1.0'],
    test_suite='nose.collector',
)
