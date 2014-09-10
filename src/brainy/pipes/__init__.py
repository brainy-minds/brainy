'''
iBRAINPipes is an integration of pipette processes into iBRAIN modules.
'''
import os
import pipette
from brainy.process import BrainyProcessError
from brainy.flags import FlagManager
import logging
logger = logging.getLogger(__name__)



class BrainyPipeFailure(Exception):
    '''Thrown when pipeline execution has to be interrupted.'''


class ProccessEndedIncomplete(BrainyPipeFailure):
    '''One of the pipe's processes failed to complete successfully.'''


class BrainyPipe(pipette.Pipe):

    def __init__(self, pipes_module, definition):
        super(BrainyPipe, self).__init__(definition)
        self.process_namespace = 'brainy.pipes'
        self.pipes_module = pipes_module
        self.has_failed = False
        self.previous_process_params = None

    def instantiate_process(self, process_description,
                            default_type=None):
        process = super(BrainyPipe, self).instantiate_process(
            process_description, default_type)
        process.name_prefix = self.name
        return process

    def get_step_name(self, process_name):
        return 'pipes-%s-%s' % (self.name, process_name)

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

    def execute_process(self, process, parameters):
        '''Add verbosity, e.g. report status using iBRAIN XML scheme'''
        step_name = self.get_step_name(process.name)
        parameters['pipes_module'] = self.pipes_module
        parameters['process_path'] = os.path.join(
            self.pipes_module._get_flag_prefix(),
            self.name,
        )
        parameters['step_name'] = step_name
        # Some modules are allowed to have limited dependency on previous
        # steps, but this is restricted. Also check unlinking in
        # get_previous_parameters().
        parameters['previous_process_params'] = self.get_previous_parameters()
        self.previous_process_params = parameters
        try:
            super(BrainyPipe, self).execute_process(process, parameters)

            if not process.is_complete:
                raise ProccessEndedIncomplete()

        except BrainyProcessError as error:
            output = ''
            if error.output:
                # Use CDATA tag this part of the XML parsable but ignore
                # unexpected characters.
                output = '<output><![CDATA[\n%s\n]]></output>' % error.output\
                    .replace(']]>', ']]&lt;')
            warning = ''
            if error.warning:
                # Optionally link the log file if found.
                if error.job_report:
                    warning = ('<warning>%s<result_file>%s</result_file>' +
                               '</warning>') % \
                        (error.warning, error.job_report)
                else:
                    warning = '<warning>%s</warning>' % error.warning

            print('''
        <status action="%(step_name)s">failed
            %(warning_message)s
            %(output_message)s
        </status>
            ''' % {
                'step_name': step_name,
                'warning_message': warning,
                'output_message': output,
            })
            # Finally, interrupt execution
            raise BrainyPipeFailure('Execution failed')


class PipesModule(FlagManager):

    def __init__(self, project):
        self.project = project
        self.pipes_namespace = 'brainy.pipes'
        self.pipes_folder_files = [
            os.path.join(self.pipes_path, filename)
            for filename in os.listdir(self.pipes_path)
        ]
        self.__flag_prefix = self.pipes_path
        self.__pipelines = None

    @property
    def scheduler(self):
        return self.project.scheduler

    @property
    def pipes_path(self):
        return self.project.path

    def _get_flag_prefix(self):
        return self.__flag_prefix

    def get_class(self, pipe_type):
        pipe_type = self.pipes_namespace + '.' + pipe_type
        module_name, class_name = pipe_type.rsplit('.', 1)
        module = __import__(module_name, {}, {}, [class_name])
        return getattr(module, class_name)

    @property
    def pipelines(self):
        if self.__pipelines is None:
            # Repopulate dictionary.
            pipes = dict()
            for definition_filename in self.pipes_folder_files:
                if not definition_filename.endswith('Pipe.json'):
                    continue
                definition = pipette.Pipe.parse_definition(definition_filename)
                cls = self.get_class(definition['type'])
                # Note that we pass itself as a pipes_module
                pipes[definition['name']] = cls(self, definition)
            self.__pipelines = self.sort_pipelines(pipes)
        return self.__pipelines

    def sort_pipelines(self, pipes):
        '''Reorder, tolerating declared dependencies found in definitions'''
        after_dag = dict()
        before_dag = dict()
        for depended_pipename in pipes:
            pipe = pipes[depended_pipename]
            if 'after' in pipe.definition:
                dependends_on = pipe.definition['after']
                if not dependends_on in after_dag:
                    after_dag[dependends_on] = list()
                after_dag[dependends_on].append(depended_pipename)
            if 'before' in pipe.definition:
                dependends_on = pipe.definition['before']
                if not dependends_on in before_dag:
                    before_dag[dependends_on] = list()
                before_dag[dependends_on].append(depended_pipename)

        def resolve_dependecy(name_a, name_b):
            # After
            if name_a in after_dag:
                if not name_b in after_dag:
                    # Second argument has no "after" dependencies.
                    if name_b in after_dag[name_a]:
                        return -1
                else:
                    # Second argument has "after" dependencies.
                    if name_b in after_dag[name_a] \
                            and name_a in after_dag[name_b]:
                        raise Exception('Recursive dependencies')
                    if name_b in after_dag[name_a]:
                        return -1
            if name_b in after_dag:
                if not name_a in after_dag:
                    # First argument has no "after" dependencies.
                    if name_a in after_dag[name_b]:
                        return 1
                else:
                    # First argument has "after" dependencies.
                    if name_a in after_dag[name_b] \
                            and name_b in after_dag[name_a]:
                        raise Exception('Recursive dependencies')
                    if name_a in after_dag[name_b]:
                        return 1
            # Before
            if name_a in before_dag:
                if not name_b in before_dag:
                    # Second argument has no "before" dependencies.
                    if name_b in before_dag[name_a]:
                        return 1
                else:
                    # Second argument has "before" dependencies.
                    if name_b in before_dag[name_a] \
                            and name_a in before_dag[name_b]:
                        raise Exception('Recursive dependencies')
                    if name_b in before_dag[name_a]:
                        return 1
            if name_b in before_dag:
                if not name_a in before_dag:
                    # First argument has no "before" dependencies.
                    if name_a in before_dag[name_b]:
                        return -1
                else:
                    # First argument has "before" dependencies.
                    if name_a in before_dag[name_b] \
                            and name_b in before_dag[name_a]:
                        raise Exception('Recursive dependencies')
                    if name_a in before_dag[name_b]:
                        return -1
            return 0

        pipenames = list(pipes.keys())
        sorted_pipenames = sorted(pipenames, cmp=resolve_dependecy)
        result = list()
        for pipename in sorted_pipenames:
            result.append(pipes[pipename])
        return result

    def execute_pipeline(self, pipeline):
        '''
        Execute passed pipeline process within the context of this
        PipesModule.
        '''
        try:
            pipeline.communicate()
        except BrainyPipeFailure:
            # Errors are reported inside individual pipeline.
            print '<!-- A pipeline has failed. Continue with the next one -->'
            pipeline.has_failed = True

    def process_pipelines(self):
        previous_pipeline = None
        for pipeline in self.pipelines:
            # Check if current pipeline is dependent on previous one.
            depends_on_previous = False
            if not previous_pipeline is None:
                if 'before' in previous_pipeline.definition:
                    depends_on_previous = \
                        previous_pipeline.definition['before'] == pipeline.name
                elif 'after' in pipeline.definition:
                    depends_on_previous = \
                        previous_pipeline.name == pipeline.definition['after']

            if depends_on_previous and previous_pipeline.has_failed:
                print('''
                 <status action="pipes-%(pipeline_name)s">paused
                    <message>Previous pipe that we depend on has failed or did not complete</message>
                 </status>
                ''' % {
                    'pipeline_name': pipeline.name,
                })
                # If previous pipeline we are dependent on has failed, then
                # mark pipeline as failed too to inform the next dependent
                # pipeline about the failure.
                pipeline.has_failed = True
                previous_pipeline = pipeline
                continue

            # Execute current pipeline.
            self.execute_pipeline(pipeline)

            # Remember as previous.
            previous_pipeline = pipeline
