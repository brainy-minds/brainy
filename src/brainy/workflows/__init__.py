import os
import shutil
import logging
logger = logging.getLogger(__name__)


WORKFLOW_PATH = os.path.join(os.path.dirname(__file__))

WORKFLOWS = {
    'canonical': [
        # iBRAIN Phase 0
        'raw_input.br',
        'illum_corr.br',
        # iBRAIN Phase 1
        'cell_profiler.br',
        # iBRAIN Phase 2
        'post_analysis.br',
    ],
    'demo': [
        'hello_world.br',
    ],
    'empty': [],
}


def bootstrap_workflow(project_path, workflow_name):
    '''
    Put in the project a standard iBRAIN workflow made of the multiple YAML
    files (.br) grouped by the `workflow_name`. By default the workflow
    called 'canonical' will be deployed.
    '''
    logger.info('Bootstrapping project with an iBRAIN workflow: {%s}' %
                workflow_name)
    if workflow_name not in WORKFLOWS:
        raise Exception('Unknown workflow: %s' % workflow_name)
    for workflow_filename in WORKFLOWS[workflow_name]:
        src_path = os.path.join(WORKFLOW_PATH, workflow_filename)
        dst_path = os.path.join(project_path, workflow_filename)
        logger.info('%s -> %s' % (src_path, dst_path))
        shutil.copy(src_path, dst_path)
        # Once this has been done, the project can be evaluated by the command:
        # > brainy run project
        # Also see brainy.project.base.BrainyProject.run()
