import re
from xml.sax.saxutils import escape as escape_xml_special_chars
from subprocess import (PIPE, Popen)


# http://www.w3.org/TR/REC-xml/#charsets
escape_exp = re.compile(u'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]+')


def invoke(command, _in=None):
    '''
    Invoke command as a new system process and return its output.
    '''
    process = Popen(command, stdin=PIPE, stdout=PIPE, shell=True,
                    executable='/bin/bash')
    if _in is not None:
        process.stdin.write(_in)
    return process.stdout.read()


def escape_xml(raw_value):
    return escape_exp.sub('', unicode(escape_xml_special_chars(raw_value)))
