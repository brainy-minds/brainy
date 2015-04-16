import os
import shutil
import logging
from findtools.find_files import (find_files, Match, MatchAnyPatternsAndTypes,
                                  MatchAllPatternsAndTypes)
from brainy.utils import get_timestamp_str
from brainy.errors import BrainyProcessError
from brainy.process.code import PythonCodeProcess
from brainy.process.decorator import (
    format_with_params, require_keys_in_description,
    require_key_in_description)
logger = logging.getLogger(__name__)



def backup_batch_folder(data_path, backups_path):
    '''Will recursively copy current BATCH to backups path'''
    # Make sure folders exist.
    if not os.path.exists(data_path):
        raise IOError('BATCH path was not found: %s' % data_path)
    if not os.path.exists(backups_path):
        raise IOError('BACKUPS path was not found: %s' % backups_path)

    # Making a backup copy.
    backuped_data_path = os.path.join(backups_path,
                                      'BATCH_%s' % get_timestamp_str())
    if os.path.exists(backuped_data_path):
        raise IOError('BACKUP destination already exists: %s' %
                      backuped_data_path)
    # Note: the destination directory must not already exist.
    shutil.copytree(data_path, backuped_data_path)


class BackupPreviousBatch(PythonCodeProcess):
    '''Backup BATCH of the successful RUN of the CellProfiller'''

    @property
    def backups_path(self):
        return self.restrict_to_safe_path(self.parameters.get(
            'backups_path',
            os.path.join(self.process_path, 'BACKUPS'),
        ))

    def put_on(self):
        super(BackupPreviousBatch, self).put_on()
        # Recreate missing BACKUPS folder path.
        if not os.path.exists(self.backups_path):
            os.makedirs(self.backups_path)

    def get_python_code(self):
        '''
        Note that the interpreter call is included by
        self.submit_python_code()
        '''
        return '''
        from brainy.pipes.Tools import backup_batch_folder

        backup_batch_folder('%(data_path)s', '%(backups_path)s')
        ''' % {
            'data_path': self.data_path,
            'backups_path': self.backups_path,
        }

    def has_data(self):
        '''
        If backups folder is empty, it means no backup was done.
        '''
        previous_backups = find_files(
            path=self.backups_path,
            match=Match(filetype='directory', name='BATCH_*'),
            recursive=False,
        )
        for item in previous_backups:
            return True
        return False


def relative_symlink(source, target):
    if source[0] != '/' or target[0] != '/':
        raise ValueError('Arguments can be only absolute pathnames.')
    if source.startswith(target):
        raise ValueError('Source includes target pathname.')
    prefix = os.path.commonprefix([source, target])
    # Test for shared prefix to avoid bugs.
    if not prefix or prefix == '/':
        raise ValueError('No common shared prefix found.')
    if not prefix.endswith('/'):
        # Cut non-dir part.
        prefix = os.path.dirname(prefix)
    cut_index = len(prefix)
    relative_source = source[cut_index:]
    if relative_source.startswith('/'):
        relative_source = relative_source[1:]
    if len(relative_source) == 0:
        relative_source = prefix
    target_dir = target[cut_index:]
    # Find relative prefix.
    depth = len(target_dir.split(os.path.sep)) - 1
    relative_prefix = os.path.sep.join(['..' for foo in range(depth)])
    relative_source = os.path.sep.join((relative_prefix, relative_source))
    # Make missing target folders.
    parent_dir = os.path.dirname(target)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    os.symlink(relative_source, target)


@require_keys_in_description('file_patterns')
class LinkFiles(PythonCodeProcess):
    '''
    Symlink or hardlink files using relative path to the current process_path.
    '''

    @property
    @format_with_params
    @require_key_in_description
    def source_location(self):
        pass

    @property
    @format_with_params
    @require_key_in_description
    def target_location(self):
        pass

    @property
    def file_type(self):
        '''By default, we link files, not folders. Use 'd' for folders.'''
        return self.description.get('file_type', 'f')

    @property
    def recursively(self):
        '''Recursively look for patterns in source_path'''
        return bool(self.description.get('recursively', False))

    def put_on(self):
        super(LinkFiles, self).put_on()
        # Create miss)ing process folder path.
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    @staticmethod
    def link(source_path, target_path, patterns, link_type='hard',
             file_type='f', recursively=False):
        '''
        Expect keys 'hardlink' and 'symlink' keys in
        description['file_patterns']. If pattern string starts and ends with
        '/' then it is a regexp, otherwise it is fnmatch.
        '''
        assert os.path.exists(source_path)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        file_matches = find_files(
            path=source_path,
            match=MatchAnyPatternsAndTypes(
                # Can also accept symlinks sources, not just files or dirs.
                filetypes=[file_type, 'l'],
                names=patterns,
            ),
            recursive=recursively,
        )
        if link_type == 'hardlink' and file_type == 'f':
            make_link = os.link
        elif link_type == 'symlink':
            # make_link = os.symlink
            make_link = relative_symlink
        else:
            raise IOError('Unsupported link type: %s' % link_type)
        for source_file in file_matches:
            link_path = os.path.join(target_path,
                                     os.path.basename(source_file))
            try:
                print 'Linking "%s" -> "%s"' % (source_file, link_path)
                make_link(source_file, link_path)
            except (OSError, IOError) as error:
                if 'File exists' in str(error):
                    message = 'Skipping, since it looks like linking was '\
                        'already done. Maybe you are trying to re-run project'\
                        ' incorrectly. Make sure to clean previous results '\
                        'before retrying.'
                    print '%s\n(Error: %s)' % (message, str(error))
                else:
                    message = 'Unknown input-output error.'
                    raise BrainyProcessError(warning=message,
                                             output=str(error))

    @staticmethod
    def build_linking_args(source_location, target_location,
                           nested_file_patterns, file_type, recursively):
        for link_type in ['hardlink', 'symlink']:
            if link_type in nested_file_patterns:
                if type(nested_file_patterns[link_type]) != list \
                        or len(nested_file_patterns[link_type]) == 0:
                    raise BrainyProcessError(
                        message='LinkFiles process requires a non empty list '
                                'of file patterns which can be match to '
                                'files in source_location.'
                    )
                args = {
                    'source_location': source_location,
                    'target_location': target_location,
                    'file_patterns': nested_file_patterns[link_type],
                    'link_type': link_type,
                    'file_type': file_type,
                    'recursively': recursively,
                }
                yield args

    def get_python_code(self):
        '''
        Note that the interpreter call is included by
        self.submit_python_code()
        '''
        assert 'hardlink' in self.file_patterns \
            or 'symlink' in self.file_patterns

        code = 'from brainy.pipes.Tools import LinkFiles\n'

        for args in LinkFiles.build_linking_args(self.source_location,
                                                 self.target_location,
                                                 self.file_patterns,
                                                 self.file_type,
                                                 self.recursively):
            code += '''LinkFiles.link(
    '%(source_location)s',
    '%(target_location)s',
    %(file_patterns)s,
    link_type='%(link_type)s',
    file_type='%(file_type)s',
    recursively=%(recursively)r,
)
''' % args
        return code

    def has_data(self):
        '''
        Check if all files matching given patterns have been linked.
        '''
        if not os.path.exists(self.target_location):
            raise BrainyProcessError(
                message='Expected target folder is not '
                        'found: %s' % self.target_location,
                message_type='warning')

        def get_name(root, name):
            return name

        # raise Exception(self.source_location)

        if 'symlink' in self.file_patterns:
            patterns = self.file_patterns['symlink']
            source_matches = list(find_files(
                path=self.source_location,
                # Match any source type, i.e. we can link any source.
                match=MatchAnyPatternsAndTypes(names=patterns),
                recursive=self.recursively,
            ))
            target_matches = list(find_files(
                path=self.target_location,
                match=MatchAnyPatternsAndTypes(
                    filetypes=['l'],
                    names=patterns,
                ),
                recursive=self.recursively,
            ))
            if len(source_matches) != len(target_matches):
                return False
            source_matches = sorted(source_matches)
            target_matches = sorted(target_matches)
            for index in range(len(target_matches)):
                points_to = os.readlink(target_matches[index])
                while points_to.startswith('../'):
                    points_to = points_to[3:]
                if not source_matches[index].endswith(points_to):
                    return False

        if 'hardlink' in self.file_patterns:
            patterns = self.file_patterns['hardlink']
            for file_type in ['d', 'f']:
                source_matches = list(find_files(
                    path=self.source_location,
                    # Match any source type, i.e. we can link any source.
                    match=MatchAllPatternsAndTypes(
                       filetypes=[file_type],
                       names=patterns,
                    ),
                    collect=get_name,
                    recursive=self.recursively,
                ))
                target_matches = list(find_files(
                    path=self.target_location,
                    match=MatchAnyPatternsAndTypes(
                        filetypes=[file_type],
                        names=patterns,
                    ),
                    collect=get_name,
                    recursive=self.recursively,
                ))
                source_matches = sorted(source_matches)
                target_matches = sorted(target_matches)
                if source_matches != target_matches:
                    return False
        return True
