import tempfile
from brainy_tests import BrainyTest
from brainy.project import BrainyProject, BrainyProjectError


class TestBrainyProject(BrainyTest):

    def test_project_already_exists(self):
        '''Test project creation'''
        output_path = tempfile.mkdtemp()
        brainy_project = BrainyProject(name='morebrain', path=output_path)
        brainy_project.create()
        self.assertRaises(BrainyProjectError, brainy_project.create)
