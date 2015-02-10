import re
import time
from xml.sax.saxutils import escape as escape_xml_special_chars
from subprocess import (PIPE, Popen)


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


def merge_dicts(a, b, path=None, overwrite=True):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                if not overwrite:
                    raise Exception('Conflict at %s' % '.'.join(path +
                                    [str(key)]))
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
