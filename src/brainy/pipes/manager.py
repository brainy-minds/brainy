import os
import shutil
import logging
import brainy.config
from brainy.flags import FlagManager
from brainy.utils import Timer
from brainy.project.report import BrainyReporter, report_data
from brainy.pipes.base import BrainyPipe
from brainy.errors import BrainyPipeFailure, ProccessEndedIncomplete
logger = logging.getLogger(__name__)


class PipesManager(FlagManager):

    def __init__(self, project):
        self.project = project
        self.pipes_folder_files = [
            os.path.join(self.project_path, filename)
            for filename in os.listdir(self.project_path)
        ]
        self.__flag_prefix = self.project_path
        self.__pipelines = None

    @property
    def scheduler(self):
        return self.project.scheduler

    @property
    def config(self):
        return self.project.config

    @property
    def project_path(self):
        return self.project.path

    @property
    def pipe_namespaces(self):
        '''
        A list of prefixes of python class names where brainy looks for pipe
        and process types.

        YAML description of the pipe workflow contains 'type' keys. Each type
        mentioned is a shorthand. `brainy` will attempt the full python type
        (class) name discovery by looking/prepending every prefix from this
        list.

        The list is flexible. It can be defined in user configuration and
        extended in framework configuration. Later this can be also extended in
        project configuration.
        '''
        return self.config['brainy']['pipe_namespaces']

    @property
    def process_namespaces(self):
        '''
        See pipe_namespaces. For simplicity

            pipe_namespaces == process_namespaces

        Separate process namespacing is envisioned for future development.
        '''
        return self.pipe_namespaces

    def _get_flag_prefix(self):
        return self.__flag_prefix

    @property
    def pipe_extension(self):
        return self.project.config['brainy']['pipe_extension']

    def get_class(self, pipe_type):
        module = None
        exceptions = list()
        for pipe_namespace in self.pipe_namespaces:
            pipe_type_ = pipe_namespace + '.' + pipe_type
            module_name, class_name = pipe_type_.rsplit('.', 1)
            try:
                # Uncomment to debug:
                # logger.info('from %s import %s' %
                #             (module_name, class_name))
                module = __import__(module_name, {}, {}, [class_name])
            except ImportError as error:
                exceptions.append(error)
                # This may lead to hiding the nested imports like
                # missing packages. So we report the list of errors if the
                # search failed.
        if module is None:
            for exception in exceptions:
                logger.warn(str(exception))
            logger.info('Tip: check that module on PYTHON PATH!')
            raise ImportError('Failed to find/import pipe type: %s in %s' %
                              (pipe_type, self.pipe_namespaces))
        return getattr(module, class_name)

    @property
    def pipelines(self):
        if self.__pipelines is None:
            # Repopulate dictionary.
            logger.info('Discovering pipelines.')
            pipes = dict()
            for definition_filename in self.pipes_folder_files:
                if not definition_filename.endswith(self.pipe_extension):
                    continue
                pipe = BrainyPipe(self)
                pipe.parse_definition_file(definition_filename)
                cls = self.get_class(pipe.definition['type'])
                # Note that we pass itself as a pipes_manager
                pipes[pipe.definition['name']] = cls(self, pipe.definition)
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
                if dependends_on not in after_dag:
                    after_dag[dependends_on] = list()
                after_dag[dependends_on].append(depended_pipename)
            if 'before' in pipe.definition:
                dependends_on = pipe.definition['before']
                if dependends_on not in before_dag:
                    before_dag[dependends_on] = list()
                before_dag[dependends_on].append(depended_pipename)

        def resolve_dependecy(name_a, name_b):
            # After
            if name_a in after_dag:
                if name_b not in after_dag:
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
                if name_a not in after_dag:
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
                if name_b not in before_dag:
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
                if name_a not in before_dag:
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
            BrainyReporter.append_report_pipe(pipeline.name)
            pipeline.communicate({'input': '{}'})
        except ProccessEndedIncomplete as process_error:
            logger.error('%s Stopped on process called: %s' %
                         (str(process_error), process_error.process.name))
            pipeline.has_failed = True  # Halt further progress
        except BrainyPipeFailure as failure:
            # Errors are reported inside individual pipeline.
            logger.error('A pipeline has failed. We can not continue.')
            logger.exception(failure)
            pipeline.has_failed = True

    def process_pipelines(self):
        BrainyReporter.start_report()
        previous_pipeline = None
        for pipeline in self.pipelines:
            # Start by expecting failure free run.
            pipeline.has_failed = False

            # Check if current pipeline is dependent on previous one.
            depends_on_previous = False
            if previous_pipeline is not None:
                if 'before' in previous_pipeline.definition:
                    depends_on_previous = \
                        previous_pipeline.definition['before'] == pipeline.name
                elif 'after' in pipeline.definition:
                    depends_on_previous = \
                        previous_pipeline.name == pipeline.definition['after']

            if depends_on_previous and previous_pipeline.has_failed:
                logger.warn(('%s is skipped. Previous pipe that we depend on'
                            ' has failed or did not complete.') %
                            pipeline.name)
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

            if pipeline.has_failed:
                logger.warning('Pipeline {%s} has failed.' % pipeline.name)
            else:
                logger.info('Pipeline {%s} run without fatal errors.' %
                            pipeline.name)

        # Finalize the report.
        BrainyReporter.finalize_report()
        BrainyReporter.save_report(self.project.report_prefix_path)
        BrainyReporter.update_or_generate_static_html(
            self.project.report_folder_path)

    def clean_pipelines_output(self):
        for pipeline in self.pipelines:
            if os.path.exists(pipeline.output_path):
                logger.warn('Recursively clean/remove subfolder: %s' %
                            pipeline.output_path)
                shutil.rmtree(pipeline.output_path)

    def run(self, command):
        '''
        This wrapper helps execute a particular command of the pipe manager.

        Such command is just a method of the class.  This approach allows to
        report elapsed time of command execution and facilitate with logging.
        '''
        if not hasattr(self, command):
            logger.error('Pipes manager does not know command called: %s' %
                         command)
            return
        try:
            # Obtain method.
            method = getattr(self, command)
            # Time method execution.
            timer = Timer()
            with timer:
                method()
            logger.info('Finished running <%s>. It took about %d (s)' % (
                        command, timer.duration_in_seconds()))
            report_data['duration_in_seconds'] = timer.duration_in_seconds()
        except Exception as error:
            # logger.error(error)
            logger.exception(error)
