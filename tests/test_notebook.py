# pylint: disable=unused-import, redefined-outer-name
"""
Tests for the overall notebook object.
"""
import datetime
import tidynotes

from .fixtures import test_notebook_dir, test_notebook


def test_create(test_notebook_dir: str) -> None:
    """Test that the notebook is created correctly."""
    tidynotes.Notebook.initialise(test_notebook_dir)
    assert tidynotes.Notebook.is_notebook(test_notebook_dir)


def test_notebook_detection_negative(test_notebook_dir: str) -> None:
    """Test that a non-notebook directory isn't identified as a notebook."""
    assert not tidynotes.Notebook.is_notebook(test_notebook_dir)


def test_create_not_overwriting(test_notebook_dir: str) -> None:
    """Test that the notebook creation doesn't overwrite existing files."""
    notebook_1 = tidynotes.Notebook.initialise(test_notebook_dir)
    notebook_1.set_config("notebook_name", "Notebook 2")
    notebook_2 = tidynotes.Notebook.initialise(test_notebook_dir)
    assert notebook_2.config["notebook_name"] == "Notebook 2"


def test_note_creation(test_notebook: tidynotes.Notebook) -> None:
    """Test that note creation works."""
    note_date = datetime.datetime(year=2021, month=1, day=24)

    assert len(test_notebook.notes) == 0
    test_notebook.make_note(note_date)
    assert len(test_notebook.notes) == 1
    test_notebook.make_note(note_date)
    assert len(test_notebook.notes) == 1


def test_note_series_creation(test_notebook: tidynotes.Notebook) -> None:
    """Test that note-series creation works."""
    note_date = datetime.datetime(year=2021, month=1, day=24)

    assert len(test_notebook.notes) == 0
    test_notebook.make_series(5, note_date)
    assert len(test_notebook.notes) == 5
    test_notebook.make_series(5, note_date)
    assert len(test_notebook.notes) == 5
