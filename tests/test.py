import unittest
import shutil, tempfile
import os
from tidynotes.notebook import Tidybook
import datetime


class TidynoteInit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_notebook_creation_explicit(self):
        book = Tidybook(self.test_dir, initialise=True)

        resource_map = book.resource_map
        paths = [os.path.join(resource_map[x], x) for x in resource_map]
        for path in paths:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, path)))

    def test_notebook_creation_implicit(self):
        book = Tidybook(self.test_dir, initialise=False)

        resource_map = book.resource_map
        paths = [os.path.join(resource_map[x], x) for x in resource_map]
        for path in paths:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, path)))

    def test_notebook_creation_explicit_cli(self):
        cmd = f'tidynotes -notedir "{self.test_dir}" -i'
        os.system(cmd)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "config.json")))

    def test_notebook_creation_implicit_cli(self):
        cmd = f'tidynotes -notedir "{self.test_dir}"'
        os.system(cmd)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "config.json")))

    def test_notebook_creation_implicit_cli_blocked(self):
        with open(os.path.join(self.test_dir, "temp.txt"), "w") as f:
            f.write(" ")
        cmd = f'tidynotes -notedir "{self.test_dir}"'
        os.system(cmd)
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "config.json")))


class TidynoteGeneration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.book = Tidybook(self.test_dir, initialise=True)
        self.file_format = "notes_%Y-%m-%d_%a.md"
        self.file_path_format = "%Y/%m"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_note_str(self):
        self.book.make_note_str("2020-01-20")
        note_path = os.path.join(
            self.test_dir, "notes", "2020", "01", "notes_2020-01-20_Mon.md"
        )
        self.assertTrue(os.path.exists(note_path))

    def test_generate_note_str_cli(self):
        cmd = f'tidynotes -notedir "{self.test_dir}" -d 2020-01-20'
        os.system(cmd)
        note_path = os.path.join(
            self.test_dir, "notes", "2020", "01", "notes_2020-01-20_Mon.md"
        )
        self.assertTrue(os.path.exists(note_path))

    def test_generate_note_seq(self):
        self.book.make_note_series(n_steps=4, start=datetime.datetime(2020, 1, 20))
        note_dir = os.path.join(self.test_dir, "notes", "2020", "01")
        days = [
            "notes_2020-01-20_Mon.md",
            "notes_2020-01-21_Tue.md",
            "notes_2020-01-22_Wed.md",
            "notes_2020-01-23_Thu.md",
        ]
        for x in days:
            self.assertTrue(os.path.exists(os.path.join(note_dir, x)))

    def test_generate_note_seq_cli(self):
        cmd = f'tidynotes -notedir "{self.test_dir}" -s 4'
        os.system(cmd)
        note_dir = os.path.join(self.test_dir, "notes")
        days = [datetime.date.today() + datetime.timedelta(days=n) for n in range(4)]
        for x in days:
            note_path = os.path.join(
                note_dir,
                x.strftime(self.file_path_format),
                x.strftime(self.file_format),
            )
            self.assertTrue(os.path.exists(note_path))

    def test_generate_note_today(self):
        self.book.make_note()
        x = datetime.datetime.now()
        note_dir = os.path.join(self.test_dir, "notes")
        note_path = os.path.join(
            note_dir, x.strftime(self.file_path_format), x.strftime(self.file_format)
        )
        self.assertTrue(os.path.exists(note_path))

    def test_generate_note_today_cli(self):
        cmd = f'tidynotes -notedir "{self.test_dir}" -g'
        os.system(cmd)
        x = datetime.datetime.now()
        note_dir = os.path.join(self.test_dir, "notes")
        note_path = os.path.join(
            note_dir, x.strftime(self.file_path_format), x.strftime(self.file_format)
        )
        self.assertTrue(os.path.exists(note_path))


if __name__ == "__main__":
    unittest.main()
