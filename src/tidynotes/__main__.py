"""
Command-line arguments to drive the notebook management tools.
"""

import argparse
import os

from .logs import setup_logging
from .notebook import Notebook


def main() -> None:
    """
    Run the tool via command-line tools.
    """

    parser = argparse.ArgumentParser(description="Markdown notebook manager.")
    parser.add_argument(
        "-notedir", type=str, help="Notebook directory path.", default=os.getcwd()
    )
    parser.add_argument(
        "-g", "--generate_note", help="Make a note for today.", action="store_true"
    )
    parser.add_argument(
        "-s", "--make_series", help="Make notes for n days in the future.", type=int
    )
    parser.add_argument(
        "-r", "--render_all", help="Render all notes.", action="store_true"
    )
    parser.add_argument(
        "-c", "--clean", help="Clean up notes in the notebook.", action="store_true"
    )
    parser.add_argument(
        "-i",
        "--initialise_notebook",
        help="Create a blank notebook in the target directory.",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--extract_project",
        help="Extracts all entries for a single project and renders them to HTML.",
    )
    parser.add_argument(
        "-a",
        "--extract_all",
        help="Extracts all entries for a each project and renders them to HTML.",
        action="store_true",
    )

    args = parser.parse_args()
    active = any(
        [
            args.initialise_notebook,
            args.clean,
            args.render_all,
            args.generate_note,
            args.make_series is not None,
            args.extract_project is not None,
        ]
    )

    if not active:
        return

    setup_logging(os.path.join(args.notedir, "TidyNotes.log"))
    if args.initialise_notebook:
        book = Notebook.initialise(args.notedir)
    else:
        if Notebook.is_notebook(args.notedir):
            book = Notebook(args.notedir)
        else:
            print("Directory is not a notebook, use the -i flag to initialise.")
            return

    if args.generate_note:
        book.make_note()
    if args.clean:
        book.clean()
    if args.render_all:
        book.render_full()
    if args.make_series is not None:
        book.make_series(args.make_series)
    if args.extract_project is not None:
        book.render_project(project_name=args.extract_project)
    if args.extract_all:
        book.render_all_projects()


if __name__ == "__main__":
    main()
