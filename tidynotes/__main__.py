import os

from tidynotes import notebook

# # TODO: These could probably be entry points too?


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Markdown notebook manager.")
    parser.add_argument(
        "notedir", type=str, help="Notebook directory path.", default=os.getcwd()
    )
    parser.add_argument(
        "-g", "--generate_note", help="Make a note for today.", action="store_true"
    )
    parser.add_argument("-d", "--make_day", help="Make notes for a specific day.")
    parser.add_argument(
        "-s", "--make_series", help="Make notes for n days in the future.", type=int
    )
    parser.add_argument(
        "-r", "--render_all", help="Render all notes.", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--clean_headings",
        help="Clean headings in the notes.",
        action="store_true",
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
    book = notebook.notebook(
        config_path=args.notedir, make_notebook=args.initialise_notebook
    )

    if args.clean_headings:
        book.clean()
    if args.render_all:
        book.render_notebook()
    if args.make_note:
        book.make_note()
    if args.make_day is not None:
        book.make_note_str(args.make_day)
    if args.make_series is not None:
        book.make_note_series(args.make_series)
    if args.extract_project is not None:
        book.render_project(args.extract_project)
    if args.extract_all:
        book.render_all_projects()


if __name__ == "__main__":
    main()
