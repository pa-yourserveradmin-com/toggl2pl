import unittest
from toggl2pl.__main__ import check_workspace


class TestCLI(unittest.TestCase):

    def test_check_workspace_list(self):
        with self.assertRaises(TypeError):
            check_workspace(workspace=list())

    def test_check_workspace_none(self):
        with self.assertRaises(TypeError):
            check_workspace(workspace=None)

    def test_check_workspace_dict(self):
        workspace = {
            'id': 1
        }
        result = check_workspace(workspace=workspace)
        self.assertEqual(workspace, result)


if __name__ == '__main__':
    unittest.main()
