import re
import time
from xml.sax.saxutils import escape as escape_xml_special_chars
from subprocess import (PIPE, Popen)
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# http://www.w3.org/TR/REC-xml/#charsets
escape_exp = re.compile(u'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]+')


def invoke(command, _in=None):
    '''
    Invoke command as a new system process and return its output.
    '''
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True,
                    executable='/bin/bash')
    if _in is not None:
        return process.communicate(input=_in)
    stdoutdata = process.stdout.read()
    stderrdata = process.stderr.read()
    return (stdoutdata, stderrdata)


def escape_xml(raw_value):
    return escape_exp.sub('', unicode(escape_xml_special_chars(raw_value)))


def merge_dicts(a, b, path=None, overwrite=True, append_lists=None):
    '''
    Merges b into a.

    append_lists is a list of paths that can be glued, e.g. [['sub', 'list']]
    '''
    if path is None:
        path = []
    if append_lists is None:
        append_lists = []
    for key in b:
        if key in a:
            sub_path = path + [str(key)]
            if isinstance(a[key], list) and isinstance(b[key], list)\
                    and sub_path in append_lists:
                a[key] = a[key] + b[key]
                continue
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], sub_path, overwrite, append_lists)
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                if not overwrite:
                    raise Exception('Conflict at %s' % '.'.join(
                                    path + [str(key)]))
        else:
            a[key] = b[key]
    return a


class Timer(object):
    '''
    timer = Timer()

    with timer:
        # Whatever you want to measure goes here
        time.sleep(2)

    print timer.duration_in_seconds()
    '''
    def __enter__(self):
        self.__start = time.time()

    def __exit__(self, type, value, traceback):
        # Error handling here
        self.__finish = time.time()

    def duration_in_seconds(self):
        return self.__finish - self.__start


def load_yaml(value):
    '''
    Take YAML string and return nested dict.

    TODO:
    Based on ruamel.yaml:
        - is a YAML parser/emitter that supports roundtrip preservation
          of comments, seq/map flow style, and map key order.
    '''
    return yaml.load(value)


def dump_yaml(value):
    '''
    Take dict and return yaml string.

    TODO: Based on ruamel.yaml:
        - is a YAML parser/emitter that supports roundtrip preservation
          of comments, seq/map flow style, and map key order.
    '''
    return yaml.dump(value, default_flow_style=True)


def replace_template_params(template_stream, parameters):
    '''
    Replace parameters in string template stream.
    '''
    return StringIO(str(template_stream.read() % parameters))


def get_timestamp_str():
    return datetime.now().strftime('%Y%m%d%H%M%S')
