import os
import json
from brainy.utils import invoke


# Set this value from the point of import.
IBRAIN_ROOT = None
_config = None

__all__ = ['get_config', 'set_root']


def set_root(new_root):
    '''
    First time get_config() is called the configuration is cached.
    You can change IBRAIN_ROOT by calling set_root only before calling it
    either as argument for get_config() or before get_config().
    Any set_root() invocation after get_config() is pointless.
    '''
    global IBRAIN_ROOT, _config
    IBRAIN_ROOT = new_root
    _config = None


def get_config(root=None):
    global _config
    if not _config is None:
        return _config
    if root is None:
        root = IBRAIN_ROOT
    if root is None:
        raise Exception('IBRAIN_ROOT is not set')
    config_file = os.path.join(root, 'etc', 'config')
    if not os.path.exists(config_file):
        raise Exception('Missing iBRAIN configuration file: %s' %
                        config_file)

    config_json = invoke('''
export IBRAIN_ROOT=%(IBRAIN_ROOT)s
. ${IBRAIN_ROOT}/etc/config
echo {
echo \\"bin_path\\": \\\"$IBRAIN_BIN_PATH\\\",
echo \\"etc_path\\": \\\"$IBRAIN_ETC_PATH\\\",
echo \\"var_path\\": \\\"$IBRAIN_VAR_PATH\\\",
echo \\"log_path\\": \\\"$IBRAIN_LOG_PATH\\\",
echo \\"database_path\\": \\\"$IBRAIN_DATABASE_PATH\\\",
echo \\"user_path\\": \\\"$IBRAIN_USER\\\",
echo \\"admin_path\\": \\\"$IBRAIN_ADMIN_EMAIL\\\",
echo \\"scheduling_engine\\": \\\"$SCHEDULING_ENGINE\\\",
echo \\"python_cmd\\": \\\"$PYTHON_CMD\\\",
echo \\"matlab_cmd\\": \\\"$MATLAB_CMD\\\",
echo \\"cellprofiler2_path\\": \\\"$CELLPROFILER2_PATH\\\"
echo }
    ''' % {'IBRAIN_ROOT': root})
    #print config_json
    config = json.loads(config_json)
    config['root'] = root
    return config


# def dump_config(config, format='json'):
#     if format == 'json':
#         return json.dumps(config)
#     elif format == 'bash':
#         # Map to bash variables


# To use externally defined brainy.modules.IBRAIN_ROOT value call set_root()
# Otherwise we try guessing from OS ENV or by importing ext_path (symlink).


# Use OS environment setting if present.
if IBRAIN_ROOT is None and 'IBRAIN_ROOT' in os.environ:
    assert os.path.exists(os.environ['IBRAIN_ROOT'])
    IBRAIN_ROOT = os.environ['IBRAIN_ROOT']

# Guessing by parsing __file__ in ext_path module.
if IBRAIN_ROOT is None:
    from ext_path import root_path
    IBRAIN_ROOT = root_path

# Note that we don't call get_config(), so there is still an option e.g. for
# a unit test to perform set_root().
