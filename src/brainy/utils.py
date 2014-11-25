import re
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
        process.stdin.write(_in)
    return process.stdout.read()


def escape_xml(raw_value):
    return escape_exp.sub('', unicode(escape_xml_special_chars(raw_value)))


def merge_dicts(a, b, path=None):
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
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
