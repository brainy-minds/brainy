import os
import shutil
import logging
from pprint import pformat


logger = logging.getLogger(__name__)


class WorkflowLocations(object):

    def __init__(self, brainy_config):
        # Merged brainy configuration including user-wide settings times
        # framework settings. See brainy.config.load_brainy_config()
        self.config = brainy_config
        self._workflows = None

    @property
    def workflow_locations(self):
        '''
        A list of multiple possible workflow locations. Each folder in the
        path has a simple format. It contains folders each
        (name of the folder == name of the workflow)
        having multiple .br files
        (pipes === YAML files with parts of the workflow description)
        '''
        return self.config['brainy']['workflows']

    @property
    def workflows(self):
        '''
        Return a dictionary that maps workflow_name -> list of .br files.
        Workflow lists are full pathnames
        '''
        if self._workflows is None:
            self._workflows = dict()
            for location in self.workflow_locations:
                if not os.path.exists(location):
                    logger.warn('Workflow location does not exists: %s' %
                                location)
                    continue
                # Each folder is a workflow.
                for workflow_name in os.listdir(location):
                    workflow_path = os.path.join(location, workflow_name)
                    if not os.path.isdir(workflow_path):
                        # Only dirs are workflows.
                        continue
                    if workflow_name not in self._workflows:
                        self._workflows[workflow_name] = list()
                    # Note: with this code we copy every file, not just
                    # *.br files with the usual pipe mask.
                    for pipe_name in os.listdir(workflow_path):
                        pipe_path = os.path.join(workflow_path, pipe_name)
                        self._workflows[workflow_name].append(pipe_path)
        return self._workflows

    def bootstrap_workflow(self, project_path, workflow_name):
        '''
        Put in the project a standard iBRAIN workflow made of the multiple YAML
        files (.br) grouped by the `workflow_name`. By default the workflow
        called 'canonical' will be deployed.
        '''
        logger.info('Bootstrapping project with an iBRAIN workflow: {%s}' %
                    workflow_name)
        if workflow_name not in self.workflows:
            logger.info('List of known workflows: ')
            logger.info(pformat(self.workflows.keys()))
            raise Exception('Unknown workflow: %s' % workflow_name)
        for pipe_filepath in self.workflows[workflow_name]:
            src_path = pipe_filepath
            dst_path = os.path.join(project_path,
                                    os.path.basename(pipe_filepath))
            logger.info('%s -> %s' % (src_path, dst_path))
            shutil.copy(src_path, dst_path)
            # Once this has been done, the project can be evaluated by the
            # command:
            # > brainy run project
            # Also see brainy.project.base.BrainyProject.run()
