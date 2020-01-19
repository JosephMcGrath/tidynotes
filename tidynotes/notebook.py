import os
import jinja2
import datetime
import markdown
import re
import json
import hashlib
import collections
import pkg_resources


class Tidybook:
    resource_map = {
        "config.json": "",
        "corrections.json": "working",
        "note.css": "templates",
        "note.md": "templates",
        "page.html": "templates",
        "render_changes.json": "working",
    }
    template_src = "templates"

    def __init__(self, config_path, initialise=None):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.initialise = initialise
        if initialise:
            self.make_notebook(config_path)
        self._read_config(config_path)
        _ = jinja2.FileSystemLoader(self.template_path)
        self.env = jinja2.Environment(loader=_)

    def _read_config(self, config_path):
        assert os.path.exists(config_path)
        if os.path.isfile(config_path):
            self.root_path = os.path.split(config_path)[0]
            self.config_path = config_path
        elif os.path.isdir(config_path):
            if len(os.listdir(config_path)) == 0:
                self.make_notebook(config_path)
            self.root_path = config_path
            self.config_path = os.path.join(config_path, "config.json")
        self.config = self.read_json(self.config_path)
        self.note_path = os.path.join(self.root_path, self.config["note_path"])
        self.template_path = os.path.join(self.root_path, self.config["template_path"])

    def _working_path(self, file_name):
        return os.path.join(self.root_path, self.config["working_path"], file_name)

    def _write(self, file_path: str, content: str, mode: str = "w"):
        "Writes a string to a file."
        dst_dir = os.path.split(file_path)[0]
        if dst_dir != "":
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

    def _write_json(self, file_path: str, content):
        self._write(file_path, json.dumps(content, indent=2))

    def read(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return text

    def is_empty(self, file_path: str, threshold: int = 0) -> bool:
        """
        Checks if a markdown note has any lines that are not a title or blank.
        A threshold of blank lines can be passed in (a negative threshold will
        always return True).
        """
        # TODO: Threshold as a part of the config file?
        if threshold < 0:
            return True
        non_empty = [
            x for x in re.findall("(?i)\n[^#][\w]+", self.read(file_path)) if x.strip()
        ]
        return len(non_empty) > threshold

    def read_json(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                return json.load(f, object_pairs_hook=collections.OrderedDict)
        else:
            return collections.OrderedDict()

    def make_note(self, date=datetime.datetime.today(), force=False):
        "Generates and writes a note for the specified date."
        date_f = self._format_date(date)
        dst_path = os.path.join(self.note_path, date_f["path"], date_f["file"])
        if force or not os.path.exists(dst_path):
            template = self.env.get_template("note.md")
            output = template.render(dates=date_f)
            self._write(dst_path, output)

    def make_note_str(self, datestr, force=False):
        "Generates and writes a note for a date specified as a string."
        self.make_note(self._parse_date(datestr), force)

    def make_note_series(
        self,
        n_steps,
        start=datetime.datetime.today(),
        step=datetime.timedelta(days=1),
        force=False,
    ):
        "Generates and writes a series of notes."
        for step_n in range(n_steps):
            self.make_note(start + step * step_n)

    def make_template_item(self, src_path, dst_path, overwrite=False):
        if not os.path.exists(dst_path) or overwrite:
            with open(dst_path, "wb") as f:
                raw = pkg_resources.resource_string(__name__, src_path)
                f.write(raw)

    def make_notebook(self, dst_dir):
        for resource_dir in {self.resource_map[x] for x in self.resource_map}:
            if resource_dir:
                os.makedirs(os.path.join(dst_dir, resource_dir), exist_ok=True)
        for template in self.resource_map:
            src_path = os.path.join(self.template_src, template)
            dst_path = os.path.join(dst_dir, self.resource_map[template], template)
            self.make_template_item(src_path, dst_path, overwrite=False)

    def _format_date(self, target_date):
        """Formats a date into useful predefined formats."""
        formats = self.config["date_formats"]
        return {x: target_date.strftime(formats[x]) for x in formats}

    def _parse_date(self, input_date):
        format_list = self.config["date_formats"]
        for format in self.config["date_formats"]:
            try:
                return datetime.datetime.strptime(input_date, format_list[format])
            except:
                pass

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
        replacement_path = self._working_path("render_changes.json")
        replacements = self.read_json(replacement_path)
        for x in replacements:
            output = re.sub(x, replacements[x], output)
        return output

    def _render_markdown_to_file(self, markdown_list, output_name):
        "Writes a list of markdown entries to HTML."
        output = [
            self._render_markdown(self._preprocess_markdown(x)) for x in markdown_list
        ]
        render_args = {**self.config, "body": "\n".join(output)}
        output = self.env.get_template("page.html").render(render_args)
        dst_dir = os.path.join(self.root_path, "rendered")
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        output_path = os.path.join(dst_dir, output_name) + ".html"
        self._write(output_path, output)
        self._log_file_info(output_path)

    def render_notebook(self):
        "Render the entire notebook to a HTML file."
        output = [self.read(path) for path in self.note_list() if self.is_empty(path)]
        self._render_markdown_to_file(output, self.config["notebook_name"])

    def render_project(self, project_name):
        "Extracts all entries for a project and writes them to a HTML file."
        # TODO: Generalise this method for tasks.
        # Check if the project name's in the replacement list.
        lookup_table = self.read_json(self._working_path("project_names.json"))
        title_name = "## " + re.sub("(^#+)", "", project_name).strip()
        if title_name in lookup_table:
            title_name = lookup_table[title_name]
        project_name = re.sub("(^#+)", "", title_name).strip()
        # Extract the project from all notes:
        markdown_extract = []
        for n, path in enumerate(self.note_list()):
            if self.is_empty(path):
                continue
            collect = False
            temp = re.split("\ufeff|\n", self.read(path))
            lines_extract = []
            title = ""
            for line in temp:
                if re.search("^# ", line):
                    title = line + "\n"
                if line.strip() == title_name:
                    collect = True
                elif re.search("^## ", line):
                    collect = False
                if collect:
                    lines_extract.append(line)
            if len(lines_extract):
                lines_extract.insert(0, title)
                markdown_extract.append("\n".join(lines_extract))
        # Render to HTML
        if len(markdown_extract):
            self._render_markdown_to_file(markdown_extract, project_name)

    def render_all_projects(self):
        "Renders a HTML output for all projects."
        temp = self._build_heading_list(self._working_path("project_names.json"), 2)
        projects = set([temp[x] for x in temp])
        for project in projects:
            self.render_project(project)

    def _log_file_info(self, file_path):
        "Logs information about a file (called after rendering an output)."
        dst_path = self._working_path("hash_log.csv")
        file_info = os.stat(file_path)
        output = [
            '"' + os.path.relpath(file_path, self.root_path) + '"',
            datetime.datetime.fromtimestamp(file_info.st_mtime).isoformat(),
            calc_sha256(file_path),
            calc_md5(file_path),
            str(file_info.st_size),
        ]
        self._write(dst_path, ",".join(output) + "\n", "a")

    def _build_heading_list(self, title_lookup_path, level=2):
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
        self._write_json(title_lookup_path, output)
        return output

    def _clean_headings(self, title_lookup_list):
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
                self._write(note_file, "\n".join(lines))

    def clean_project_list(self):
        "Cleans up project names in the notebook."
        file_path = self._working_path("project_names.json")
        self._clean_headings(self._build_heading_list(file_path, 2))

    def clean_task_list(self):
        "Cleans up task names in the notebook."
        file_path = self._working_path("task_names.json")
        self._clean_headings(self._build_heading_list(file_path, 3))

    def corrections(self):
        "Applies regex replacements to notes."
        replacements = self.read_json(self._working_path("corrections.json"))
        for note_file in self.note_list():
            write = False
            raw = self.read(note_file)
            output = self.read(note_file)
            for replacement in replacements:
                if re.search(replacement, output):
                    output = re.sub(replacement, replacements[replacement], output)
            if raw != output:
                self._write(note_file, output)

    def clean(self):
        self.clean_project_list()
        self.clean_task_list()
        self.corrections()


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
