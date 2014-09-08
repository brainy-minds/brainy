import os
import shutil
import logging
logger = logging.getLogger(__name__)


WORKFLOW_PATH = os.path.join(os.path.dirname(__file__))
CANNONICAL_WORKFLOW = [
    # iBRAIN Phase 0
    'raw_input.br',
    'illum_corr.br',
    # iBRAIN Phase 1
    'cell_profiler.br',
    # iBRAIN Phase 2
    'post_analysis.br',
]


def bootstrap_workflow(project_path):
    logger.info('Bootstraping project with a standard iBRAIN workflow.')
    for workflow_filename in CANNONICAL_WORKFLOW:
        src_path = os.path.join(WORKFLOW_PATH, workflow_filename)
        dst_path = os.path.join(project_path, workflow_filename)
        logger.info('%s -> %s' % (src_path, dst_path))
        shutil.copy(src_path, dst_path)
