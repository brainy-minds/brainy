'''
iBRAINPipes is an integration of pipette processes into iBRAIN modules.
'''
from __future__ import with_statement
import os
import pipette
import logging
import pprint
import brainy.config
from brainy.errors import (BrainyProcessError, ProccessEndedIncomplete,
                           BrainyPipeFailure)
from brainy.project.report import BrainyReporter
logger = logging.getLogger(__name__)


class BrainyPipe(pipette.Pipe):

    def __init__(self, pipes_manager, definition=None):
        process_namespaces = brainy.config.load_process_namespaces()
        super(BrainyPipe, self).__init__(process_namespaces, definition)
        self.pipes_manager = pipes_manager
        self.has_failed = False
        self.previous_process_params = None

    @property
    def pipe_extension(self):
        return self.pipes_manager.pipe_extension

    @property
    def output_path(self):
        return os.path.join(self.pipes_manager.project_path, self.name)

    def instantiate_process(self, process_description,
                            default_type=None):
        process = super(BrainyPipe, self).instantiate_process(
            process_description, default_type)
        process.name_prefix = self.name
        return process

    def get_step_name(self, process_name):
        return '%s-%s' % (self.name, process_name)

    def get_previous_parameters(self):
        if self.previous_process_params is None:
            return
        if not self.previous_process_params['previous_process_params'] is None:
            # Avoid chaining the back up to the first process. Such linking
            # can motivate a very bad programming practices. Only one step
            # before is allowed to memorize. Everything else is just to
            # complicated. So we unlink previous of previous here.
            self.previous_process_params['previous_process_params'] = None
        return self.previous_process_params

    def get_process_path(self):
        return os.path.join(
            self.pipes_manager._get_flag_prefix(),
            self.name,
        )

    def get_process_parameters(self):
        parameters = dict()
        parameters['pipes_manager'] = self.pipes_manager
        parameters['process_path'] = self.get_process_path()
        # Update them with project-wide parameters
        project = self.pipes_manager.project
        logger.info('Applying project-wide parameters.')
        logger.debug(pprint.pformat(project.config['project_parameters']))
        parameters.update(project.config['project_parameters'])
        return parameters

    def execute_process(self, process, parameters):
        '''
        Execute process as a step in brainy pipeline. Add verbosity, e.g.
        report status using brainy project report scheme.
        '''
        parameters = self.get_process_parameters()
        # Set step name.
        step_name = self.get_step_name(process.name)
        logger.info('Executing step {%s}' % step_name)
        parameters['step_name'] = self.get_step_name(process.name)
        # Some modules are allowed to have limited dependency on previous
        # steps, but this is restricted. Also check unlinking in
        # get_previous_parameters().
        parameters['previous_process_params'] = self.get_previous_parameters()
        self.previous_process_params = parameters

        BrainyReporter.append_report_process(process.name)

        try:
            super(BrainyPipe, self).execute_process(process, parameters)

        except BrainyProcessError as error:
            # See brainy.errors
            error_is_fatal = False
            if 'message_type' in error.extra:
                if error.extra['message_type'] == 'error':
                    error_is_fatal = True
                del error.extra['message_type']
            if 'error_type' in error.extra:
                BrainyReporter.append_known_error(
                    message=str(error),
                    **error.extra)
            else:
                BrainyReporter.append_unknown_error(
                    message=str(error),
                    **error.extra)
            # Finally, interrupt execution if we error is fatal (default).
            if error_is_fatal:
                logger.exception(error)
                if 'job_report' in error.extra:
                    logger.error('Inspect error details in job report: %s' %
                                 error.extra['job_report'])
                raise BrainyPipeFailure('Execution failed')

        finally:

            if not process.is_complete:
                raise ProccessEndedIncomplete(process=process)
