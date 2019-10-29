import os
import jinja2
import datetime
import markdown
import re
import json
import hashlib

# TODO: Accept command-line inputs,
# TODO: Replacements at the time of rendering,
# TODO: Heading management (project / task names),
# TODO: To-do list,
# TODO: Extract (& render) all entires under a single heading,
# TODO: Cache rendered html to speed up repeated rendering,
# TODO: Formatting adjustments,
# TODO: Create notebooks in a target folder,


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
        with open(self.config_path) as f:
            self.config = json.load(f)
        self.note_path = os.path.join(self.root_path, self.config["note_path"])
        self.template_path = os.path.join(self.root_path, self.config["template_path"])
        self.notebook_name = self.config["notebook_name"]
        self.working_path = self.config["working_path"]

    def write(self, file_path: str, content: str, mode: str = "w"):
        "Writes a string to a file."
        dst_dir = os.path.split(file_path)[0]
        if dst_dir != "":
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
        with open(file_path, mode, encoding="utf-8") as f:
            return f.write(content)

    def read(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return text

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
        md = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists"])
        return md.convert(markdown_text)

    def _preprocess_markdown(self, markdown_text):
        lines = markdown_text.split("\n")
        # Add a level to the titles
        lines = [re.sub("^#", "##", x) for x in lines]
        return "\n".join(lines)

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
        output_path = os.path.join(self.root_path, self.notebook_name) + ".html"
        self.write(output_path, output)
        self.log_file_info(output_path)

    def log_file_info(self, file_path):
        dst_path = os.path.join(self.root_path, self.working_path, "hash_log.csv")
        file_info = os.stat(file_path)
        output = [
            os.path.relpath(file_path, self.root_path),
            datetime.datetime.fromtimestamp(file_info.st_ctime).isoformat(),
            calc_sha256(file_path),
            calc_md5(file_path),
            str(file_info.st_size),
        ]
        self.write(dst_path, ",".join(output) + "\n", "a")


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
    book = notebook(config_path=os.path.join(os.getcwd(), "test"))
    book.make_note()
    book.render_notebook()
