import os
import jinja2
import datetime
import markdown
import re
import json
import hashlib
import collections

# TODO: Replacements at the time of rendering,
# TODO: To-do list,
# TODO: Extract (& render) all entires under a single heading,
# TODO: Cache rendered html to speed up repeated rendering,
# TODO: Formatting adjustments,
# TODO: Create notebooks in a target folder (config & templates),
# TODO: Backup files to a zip folder,
# TODO: Option to render to multiple locations,
# TODO: Method to generate a working path,


class notebook:
    def __init__(self, config_path):
        self.read_config(config_path)
        _ = jinja2.FileSystemLoader(self.template_path)
        self.env = jinja2.Environment(loader=_)

    def read_config(self, config_path):
        if os.path.isfile(config_path):
            self.root_path = os.path.split(config_path)[0]
            self.config_path = config_path
        elif os.path.isdir(config_path):
            self.root_path = config_path
            self.config_path = os.path.join(config_path, "config.json")
        self.config = self.read_json(self.config_path)
        self.note_path = os.path.join(self.root_path, self.config["note_path"])
        self.template_path = os.path.join(self.root_path, self.config["template_path"])

    def write(self, file_path: str, content: str, mode: str = "w"):
        "Writes a string to a file."
        dst_dir = os.path.split(file_path)[0]
        if dst_dir != "":
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
        with open(file_path, mode, encoding="utf-8") as f:
            return f.write(content)

    def write_json(self, file_path: str, content):
        self.write(file_path, json.dumps(content, indent=2))

    def read(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return text

    def read_json(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path) as f:
                return json.load(f, object_pairs_hook=collections.OrderedDict)
        else:
            return collections.OrderedDict()

    def make_note(self, date=datetime.datetime.today(), force=False):
        dates = self.format_date(date)
        dst_path = os.path.join(self.note_path, dates["path"], dates["file"])
        if force or not os.path.exists(dst_path):
            template = self.env.get_template("note.md")
            output = template.render(dates=self.format_date(date))
            self.write(dst_path, output)

    def format_date(self, target_date):
        """Formats a date into useful predefined formats."""
        formats = self.config["date_formats"]
        return {x: target_date.strftime(formats[x]) for x in formats}

    def note_list(self):
        """
        Returns a list of all the markdown files in the notes folder.

        Notes are sorted by their file names (not paths).
        """
        files = [
            os.path.join(dp, f)
            for dp, _, filenames in os.walk(self.note_path)
            for f in filenames
            if os.path.splitext(f)[1].lower() == ".md"
        ]
        return sorted(files, key=lambda x: os.path.split(x)[-1])

    def _render_markdown(self, markdown_text) -> str:
        "Render provided markdown to a HTML string."
        md = markdown.Markdown(
            extensions=["fenced_code", "tables", "sane_lists", "admonition"]
        )
        return md.convert(markdown_text)

    def _preprocess_markdown(self, markdown_text):
        lines = markdown_text.split("\n")
        # Add a level to the titles
        lines = [re.sub("^#", "##", x) for x in lines]
        output = "\n".join(lines)

        # Render-time replacements
        replacement_path = os.path.join(
            self.root_path, self.config["working_path"], "render_changes.json"
        )
        replacements = self.read_json(replacement_path)
        for x in replacements:
            output = re.sub(x, replacements[x], output)
        return output

    def render_notebook(self):
        "Render the entire notebook to a HTML file."
        paths = self.note_list()
        output = [None] * len(paths)
        for n, path in enumerate(paths):
            output[n] = self._render_markdown(
                self._preprocess_markdown(self.read(path))
            )
        render_args = {**self.config, "body": "\n".join(output)}
        output = self.env.get_template("page.html").render(render_args)
        output_path = (
            os.path.join(self.root_path, self.config["notebook_name"]) + ".html"
        )
        self.write(output_path, output)
        self.log_file_info(output_path)

    def log_file_info(self, file_path):
        dst_path = os.path.join(
            self.root_path, self.config["working_path"], "hash_log.csv"
        )
        file_info = os.stat(file_path)
        output = [
            os.path.relpath(file_path, self.root_path),
            datetime.datetime.fromtimestamp(file_info.st_mtime).isoformat(),
            calc_sha256(file_path),
            calc_md5(file_path),
            str(file_info.st_size),
        ]
        self.write(dst_path, ",".join(output) + "\n", "a")

    def build_heading_list(self, title_lookup_path, level=2):
        "Builds a dictionary of all headings in the notebook."
        projects = self.read_json(title_lookup_path)
        pattern = re.compile("^#{level} ".format(level="{" + str(level) + "}"))
        for note_file in self.note_list():
            lines = self.read(note_file).split("\n")
            for project in [x for x in lines if re.search(pattern, x)]:
                project = project.strip()
                if project not in projects:
                    projects[project] = project
        output = collections.OrderedDict()
        for x in sorted(projects):
            output[x] = projects[x]
        self.write_json(title_lookup_path, output)
        return output

    def clean_headings(self, title_lookup_list):
        "Uses a provided lookup list to replace titles in the notebook."
        title_replace = {x for x in title_lookup_list if x != title_lookup_list[x]}
        if len(title_replace) == 0:
            return None

        for note_file in self.note_list():
            write = False
            lines = self.read(note_file).split("\n")
            for n, x in enumerate(lines):
                x = x.strip()
                if x in title_replace:
                    write = True
                    lines[n] = title_lookup_list[x] + "\n"
            if write:
                self.write(note_file, "\n".join(lines))

    def clean_project_list(self):
        file_path = os.path.join(
            self.root_path, self.config["working_path"], "project_names.json"
        )
        self.clean_headings(self.build_heading_list(file_path, 2))

    def clean_task_list(self):
        file_path = os.path.join(
            self.root_path, self.config["working_path"], "task_names.json"
        )
        self.clean_headings(self.build_heading_list(file_path, 3))

    def clean(self):
        self.clean_project_list()
        self.clean_task_list()


def hash_file(path, algorithm, buffer_size=65536):
    "Generic function to calculate the hash of a file."
    with open(path, "rb") as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            algorithm.update(data)
    return algorithm.hexdigest()


def calc_sha256(path, buffer_size=65536):
    "Calculates the SHA256 of a file."
    return hash_file(path, hashlib.sha256(), buffer_size)


def calc_md5(path, buffer_size=65536):
    "Calculates the MD5 of a file."
    return hash_file(path, hashlib.md5(), buffer_size)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Markdown notebook manager.")
    parser.add_argument("notedir", type=str, help="Notebook directory path.")
    parser.add_argument(
        "-m", "--make_note", help="Make a note for today.", action="store_true"
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

    args = parser.parse_args()
    book = notebook(config_path=args.notedir)

    if args.clean_headings:
        book.clean()
    if args.render_all:
        book.render_notebook()
    if args.make_note:
        book.make_note()
