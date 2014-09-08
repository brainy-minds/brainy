import os
import logging
logger = logging.getLogger(__name__)
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from brainy.version import brainy_version
from brainy.workflows import bootstrap_workflow


YAML_CONFIG_TPL = '''
# brainy project config
brainy_version = '%(brainy_version)s'

# These parameters will affect the whole project. In particular, that defines
# how jobs in every step of each pipe will be submitted, which folders names
# and locations are used, etc.
parameters:
    - job_submission_queue: '8:00'
    - job_resubmission_queue: '36:00'
    - batch_path: 'data_of_{name}'
    - tiff_path: 'images_of_{name}'

''' % {
    'brainy_version': brainy_version,
}
YAML_CONFIG_NAME = '.brainy'


class BrainyProjectError(Exception):
    '''Thrown by brainy project if the logic goes wrong.'''


class BrainyProject(object):

    def __init__(self, name, path):
        self.name = name
        if os.path.basename(path) != name:
            # Append name to full path of the project folder if it is not
            # ending with such.
            self.path = os.path.join(path, name)
        else:
            self.path = path
        self.config = None

    def create(self):
        # Make project dir.
        if not os.path.exists(self.path):
            logger.info('Creating new project folder: %s' % self.path)
            os.mkdir(self.path)
        else:
            raise BrainyProjectError('Project folder already exists: %s' %
                                     self.path)
        # Put basic YAML config during project creation. This is required for
        # project to be valid. We will also check version compatibility.
        with open(self.config_path, 'w+') as config_file:
            config_file.write(YAML_CONFIG_TPL)
        # Bootstrap project with a standard iBRAIN workflow.
        bootstrap_workflow(self.path)

    @property
    def config_path(self):
        return os.path.join(self.path, YAML_CONFIG_NAME)

    def is_a_valid_project_folder(self):
        return os.path.exists(self.config_path)

    def load_config(self):
        with open(self.config_path) as stream:
            self.config = yaml.load(stream, Loader=Loader)
