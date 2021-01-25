"""
Shared test fixtures.
"""

import tempfile
from typing import Generator

import pytest
import tidynotes


@pytest.fixture
def test_notebook_dir() -> Generator[str, None, None]:
    """Make a notebook directory."""
    with tempfile.TemporaryDirectory("tidynotes") as working_dir:
        yield working_dir


@pytest.fixture
def test_notebook() -> Generator[tidynotes.Notebook, None, None]:
    """Make an empty notebook."""
    with tempfile.TemporaryDirectory("tidynotes") as working_dir:
        yield tidynotes.Notebook.initialise(working_dir)
