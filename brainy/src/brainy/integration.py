import os
import logging
logger = logging.getLogger(__name__)
from sh import touch
from brainy.pipes import PipesModule


class CompatiblePipesModule(PipesModule):
    '''Brainy pipes module with backwards compatibility with iBRAIN.'''

    @property
    def stage_complete_flagpath(self):
        return os.path.join(self.env['plate_path'],
                            'iBRAIN_Stage_1.completed')

    def complete_stage_one(self):
        '''
        Try to complete stage_one phase of iBRAIN by creating a respective
        flag, so that the rest of iBRAIN logic can kick-in the processing.
        '''
        if os.path.exists(self.stage_complete_flagpath):
            logger.info('Found a flag. Stage one is completed.')
            return
        all_pipelines_are_complete = True
        for pipeline in self.pipelines:
            for process in pipeline.chain:
                if not process.is_complete:
                    all_pipelines_are_complete = False
                    break
            if not all_pipelines_are_complete:
                break
        # All pipelines are complete.
        if all_pipelines_are_complete:
            logger.info('All pipelines of stage one are complete. '
                        'Creating a flag.')
            touch(self.stage_complete_flagpath)
        else:
            logger.info('Not all pipelines of stage one are complete.')
