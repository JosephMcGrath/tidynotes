# pylint: disable=unused-import, redefined-outer-name
"""
Tests for the CLI architecture.
"""
import os

import tidynotes

from .fixtures import test_notebook_dir


def test_create_cli(test_notebook_dir: str) -> None:
    """Test creation of a notebook in the command-line."""
    cmd = f'tidynotes -notedir "{test_notebook_dir}" -i'
    os.system(cmd)
    assert tidynotes.Notebook.is_notebook(test_notebook_dir)


def test_create_cli_blocked(test_notebook_dir: str) -> None:
    """Test creation of a notebook in the command-line."""
    cmd = f'tidynotes -notedir "{test_notebook_dir}"'
    os.system(cmd)
    assert not tidynotes.Notebook.is_notebook(test_notebook_dir)


def test_note_creation_cli(test_notebook_dir: str) -> None:
    """Test creation of a note in the command-line."""
    cmd = f'tidynotes -notedir "{test_notebook_dir}" -i'
    os.system(cmd)

    notebook = tidynotes.Notebook(test_notebook_dir)
    assert len(notebook.notes) == 0

    cmd = f'tidynotes -notedir "{test_notebook_dir}" -g'
    os.system(cmd)

    notebook.refresh()
    assert len(notebook.notes) == 1


def test_note_series_creation_cli(test_notebook_dir: str) -> None:
    """Test that note-series creation works in the command-line."""
    cmd = f'tidynotes -notedir "{test_notebook_dir}" -i'
    os.system(cmd)

    notebook = tidynotes.Notebook(test_notebook_dir)
    assert len(notebook.notes) == 0

    cmd = cmd = f'tidynotes -notedir "{test_notebook_dir}" -s 4'
    os.system(cmd)

    notebook.refresh()
    assert len(notebook.notes) == 4
