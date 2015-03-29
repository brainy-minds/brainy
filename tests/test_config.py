import unittest
from brainy.utils import merge_dicts, load_yaml
from brainy.config import merge_config
from pprint import pprint


FOO = '''
#Some foo YAML with comments

a_key: "value"

# comment for the second key
another_key: "value"

sub_key:
    points_to_list: ['foo']

'''

BAR = '''
#Some foo YAML with comments

some_key: "value"

sub_key:
    points_to_list: ['bar']

'''


class BrainyConfigTest(unittest.TestCase):

    def test_merging(self):
        '''
        Test the the proper merging of configs: deep and specific path
        treatment.
        '''
        merged_pathnames = [
            ['sub_key', 'points_to_list'],
        ]
        foo = load_yaml(FOO)
        bar = load_yaml(BAR)
        result = merge_dicts(foo, bar, append_lists=merged_pathnames)
        # pprint(result)
        assert result['sub_key']['points_to_list'] == ['foo', 'bar']

