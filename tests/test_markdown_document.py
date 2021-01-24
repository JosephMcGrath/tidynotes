import pytest
from tidynotes.mardown_document import MarkdownPart


def test_simple_note() -> None:
    """Test for simple note creation."""
    title = "Test Title"
    body = "This is the note body\n"

    test_note = MarkdownPart(f"# {title}\n\n{body}")

    assert test_note.title == title
    assert test_note.body == body
    assert len(test_note.parts) == 0


def test_stub() -> None:
    """Tests for stub note check."""
    title = "Test Title"
    body = ""
    test_note = MarkdownPart(f"# {title}\n\n{body}")
    assert test_note.is_stub()

    title = "Test Title"
    body = "."
    test_note = MarkdownPart(f"# {title}\n\n{body}")
    assert not test_note.is_stub()


def test_replacement() -> None:
    """Check text replacement without regex."""
    title = "Test Title"
    body = "Hello world, this isn't a test!\n"
    test_note = MarkdownPart(f"# {title}\n\n{body}")
    test_note.make_replacement("isn't", "is", regex=False)

    assert test_note.body == "Hello world, this is a test!\n"


def test_replacement_regex() -> None:
    """Check text replacement with regex."""
    title = "Test Title"
    body = "Hello world, this isn't a test!\n"
    test_note = MarkdownPart(f"# {title}\n\n{body}")
    test_note.make_replacement("isn't", "is", regex=True)

    assert test_note.body == "Hello world, this is a test!\n"
