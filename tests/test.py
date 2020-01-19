import unittest
import shutil, tempfile
import os
from tidynotes.notebook import Tidybook


class TidynoteInit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_notebook_creation_explicit(self):
        book = Tidybook(self.test_dir, initialise=True)

        resource_map = {
            "config.json": "",
            "corrections.json": "working",
            "note.css": "templates",
            "note.md": "templates",
            "page.html": "templates",
            "render_changes.json": "working",
        }
        # resource_map = book.resource_map
        paths = [os.path.join(resource_map[x], x) for x in resource_map]
        for path in paths:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, path)))

    def test_notebook_creation_implicit(self):
        book = Tidybook(self.test_dir, initialise=False)

        resource_map = {
            "config.json": "",
            "corrections.json": "working",
            "note.css": "templates",
            "note.md": "templates",
            "page.html": "templates",
            "render_changes.json": "working",
        }
        # resource_map = book.resource_map
        paths = [os.path.join(resource_map[x], x) for x in resource_map]
        for path in paths:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, path)))


if __name__ == "__main__":
    unittest.main()
