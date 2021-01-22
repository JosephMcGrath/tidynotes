"""
Utility for managing an entire notebook.

There should be no direct modification of markdown here, that's in MarkdownPart.
"""

import datetime
import glob
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import jinja2
import pkg_resources

from .logs import LOG_NAME
from .mardown_document import MarkdownPart

# TODO : Linting etc
# TODO : Documentation template.
# TODO : Update tests (test the CLI!)
# TODO : Hash logs


class Notebook:
    """
    A notebook of markdown documents, creates, cleans and renders the notebook to HTML.
    """

    template_dir = "templates"
    note_dir = "notes"
    working_dir = "working"
    config_name = "config.json"
    output_dir = "rendered"

    def __init__(self, notebook_dir: str) -> None:
        logger = self._make_logger()
        self.root_dir = os.path.abspath(notebook_dir)
        self.config = self._read_config()
        if "notebook_name" not in self.config:
            self.set_config("notebook_name", "TidyNotes notebook.")

        _ = jinja2.FileSystemLoader(os.path.join(self.root_dir, self.template_dir))
        self.env = jinja2.Environment(loader=_)

        self.notes = self.read_notes()

        logger.info("Set up notebook in %s.", self.root_dir)

    @classmethod
    def initialise(cls, notebook_dir: str) -> "Notebook":
        """
        Create a notebook in the provided directory.
        """
        logger = logging.getLogger(LOG_NAME)
        logger.info("Creating notebook in [%s].", notebook_dir)
        template_list = {
            cls.config_name: "",
            "corrections.json": cls.working_dir,
            "note.css": cls.template_dir,
            "note.md": cls.template_dir,
            "page.html": cls.template_dir,
            "render_changes.json": cls.working_dir,
        }

        for template, folder in template_list.items():
            dst_dir = os.path.join(notebook_dir, folder)
            dst_path = os.path.join(dst_dir, template)

            if os.path.exists(dst_path):
                logger.warning('"%s" already exists.', dst_path)
                continue
            logger.debug('Creating "%s".', template)

            os.makedirs(dst_dir, exist_ok=True)
            src_path = os.path.join("templates", template)
            raw = pkg_resources.resource_string(__name__, src_path)

            with open(dst_path, "wb") as file_out:
                raw = pkg_resources.resource_string(__name__, src_path)
                file_out.write(raw)

        return cls(notebook_dir)

    @classmethod
    def is_notebook(cls, notebook_dir: str) -> bool:
        """Checks if the directory is a valid notebook."""
        config_path = os.path.join(notebook_dir, cls.config_name)
        if not os.path.exists(config_path):
            return False
        config = read_json(config_path)
        if not isinstance(config, dict):
            return False
        return "notebook_name" in read_json(config_path)

    def read_notes(self) -> List[MarkdownPart]:
        """Read all notes from files."""
        logger = self._make_logger()
        logger.debug("Reading notes.")
        note_pattern = os.path.join(self.root_dir, self.note_dir, "**", "*.md")
        notes = []
        for path in glob.glob(note_pattern, recursive=True):
            temp = MarkdownPart.from_file(path)
            if temp.is_stub():
                logger.debug('"%s" is a stub.', path)
                continue
            notes.append(temp)
        logger.debug("Loaded %s notes.", len(notes))
        return notes

    def make_note(
        self, date: datetime.datetime = datetime.datetime.today(), force: bool = False
    ) -> None:
        """Generates and writes a note for the specified date."""
        logger = self._make_logger("Generation")
        logger.debug("Generating a note for %s.", date)

        date_format = str(self.config["note_file_format"])
        dst_path = os.path.join(
            self.root_dir, self.note_dir, date.strftime(date_format)
        )
        os.makedirs(os.path.split(dst_path)[0], exist_ok=True)
        if force or not os.path.exists(dst_path):
            template = self.env.get_template("note.md")
            output = MarkdownPart(template.render(date=date))
            output.meta["note_for"] = date
            output.meta["notebook"] = self.config["notebook_name"]
            output.to_file(dst_path)
            logger.debug("Generated note")
            self.notes.append(MarkdownPart.from_file(dst_path))
        else:
            logger.debug("Note already exists - skipping.")
        logger.debug("Finished writing note.")

    def make_series(
        self,
        days: int = 7,
        starting: datetime.datetime = datetime.datetime.today(),
        force: bool = False,
    ) -> None:
        """Generate a series of notes for `days` number of days."""
        for _ in range(days):
            self.make_note(starting, force=force)
            starting += datetime.timedelta(days=1)

    def _make_logger(self, sub_log: Optional[str] = None) -> logging.Logger:
        """Get the logger for the notebook, with an optional sub-log name."""
        if isinstance(sub_log, str):
            log_name = f"{LOG_NAME}.{sub_log}"
        else:
            log_name = LOG_NAME
        return logging.getLogger(log_name)

    def _read_config(self) -> Dict[str, Union[str, int]]:
        logger = self._make_logger()
        config_path = os.path.join(self.root_dir, self.config_name)
        logger.debug("Reading config from %s.", config_path)

        if not os.path.exists(config_path):
            message = (
                "Config path doesn't exist. Maybe it needs to be initialised first?"
                f" The path given was {config_path}"
            )
            logger.error(message)
            raise RuntimeError(message)

        config = read_json(config_path)
        logger.debug("Finished reading config.")
        return config

    def set_config(self, item_name: str, item_value: Any) -> None:
        """Set an item in the notebook config (including config file)."""
        self.config[item_name] = item_value
        write_json(self.config, os.path.join(self.root_dir, self.config_name))

    def clean(self) -> None:
        """General cleanup operations on the notebook."""
        logger = self._make_logger("Cleanup")
        logger.info("Cleaning up all notes.")
        self.update_projects_and_tasks()
        self.text_corrections()
        for this_note in self.notes:
            this_note.to_file(this_note.meta[".file"]["path"])
        logger.info("Finished cleaning notes.")

    def extract_project(self, pattern: str) -> List[MarkdownPart]:
        """Extract all entries for a project."""
        logger = self._make_logger()
        logger.debug('Extracting notes for "%s".', pattern)
        output = []
        for this_note in self.notes:
            for part in this_note.extract_parts(pattern):
                part.title = this_note.title
                part.set_level(2)
                output.append(part)
        return output

    def update_projects_and_tasks(self) -> None:
        """
        Build a list of projects/tasks and replace existing ones based on a mapping.

        The mappings are stored in JSON files called "projects" and "tasks".
        """
        projects = read_json(self._working_path("projects.json"))
        tasks = read_json(self._working_path("tasks.json"))

        new_projects, new_tasks = self._make_part_list()
        for this_project in new_projects:
            if this_project not in projects:
                projects[this_project] = this_project
        for this_tasks in new_tasks:
            if this_tasks not in tasks:
                tasks[this_tasks] = this_tasks

        for this_note in self.notes:
            this_note.replace_title(projects, level=2)
            this_note.replace_title(tasks, level=3)

        write_json(projects, self._working_path("projects.json"))
        write_json(tasks, self._working_path("tasks.json"))

    def text_corrections(self) -> None:
        """Apply each regex replacement pattern in corrections.json to all notes."""
        corrections = read_json(self._working_path("corrections.json"))
        for pattern, replacement in corrections.items():
            for this_note in self.notes:
                this_note.make_replacement(pattern, replacement)

    def _make_part_list(self) -> Tuple[List[str], List[str]]:
        """Generate a list of projects and tasks in the notebook."""
        projects = set()
        tasks = set()
        for this_note in self.notes:
            projects.update([x.title for x in this_note.parts])
            for this_project in this_note.parts:
                tasks.update([x.title for x in this_project.parts])

        return (sorted(list(projects)), sorted(list(tasks)))

    def _working_path(self, file_name: str) -> str:
        return os.path.join(self.root_dir, self.working_dir, file_name)

    def render_full(self, dst_path: Optional[str] = None) -> None:
        """Render all notes into a single HTML file."""
        logger = self._make_logger("Rendering")
        logger.info('Rendering full notes to HTML at "%s".', dst_path)
        if dst_path is None:
            dst_path = os.path.join(
                self.root_dir, self.output_dir, f"{self.config['notebook_name']}.html"
            )
        self._render(
            notes=self.notes, title=str(self.config["notebook_name"]), dst_path=dst_path
        )
        logger.info("Finished redering full notes.")

    def render_project(self, project_name: str, dst_path: Optional[str] = None) -> None:
        """Render a single project to a HTML file."""
        logger = self._make_logger("Rendering")
        logger.info('Rendering project "%s" to HTML at "%s".', project_name, dst_path)
        if dst_path is None:
            dst_path = os.path.join(
                self.root_dir, self.output_dir, f"{project_name}.html"
            )
        self._render(
            notes=self.extract_project(project_name),
            title=project_name,
            dst_path=dst_path,
        )
        logger.info("Finished redering project.")

    def render_all_projects(self, dst_dir: Optional[str] = None) -> None:
        """Render all projects to their own HTML file."""
        logger = self._make_logger("Rendering")
        logger.info("Rendering all projects to their own output.")

        if dst_dir is None:
            dst_dir = os.path.join(self.root_dir, self.output_dir)

        projects, _ = self._make_part_list()
        for this_project in projects:
            dst_path = os.path.join(dst_dir, f"{this_project}.html")
            self.render_project(this_project, dst_path)
        logger.info("Finished all rendering projects.")

    def _render(self, notes: List[MarkdownPart], title: str, dst_path: str) -> None:
        logger = self._make_logger("Rendering")
        logger.debug("Combining %s parts for rendering.", len(notes))
        document = MarkdownPart(f"# {title}")
        for part in notes:
            document.add_part(part)

        logger.debug("Making render-time corrections.")
        corrections = read_json(self._working_path("render_changes.json"))
        for pattern, replacement in corrections.items():
            document.make_replacement(pattern, replacement)

        logger.debug("Rendering template")
        output = self.env.get_template("page.html").render(
            **self.config, document=document, title=title
        )

        logger.debug("Writing to disk.")
        with open(dst_path, "w", encoding="utf-8") as file:
            file.write(output)
        self._log_file_info(dst_path)
        logger.debug("Finished rendering.")

    def _log_file_info(self, file_path: str) -> None:
        """Logs information about a file (called after rendering an output)."""
        logger = self._make_logger()
        logger.debug("Collating information on %s.", file_path)
        dst_path = self._working_path("hash_log.csv")
        file_info = os.stat(file_path)
        output = [
            '"' + os.path.relpath(file_path, self.root_dir) + '"',
            datetime.datetime.fromtimestamp(file_info.st_mtime).isoformat(),
            calc_sha256(file_path),
            calc_md5(file_path),
            str(file_info.st_size),
        ]
        with open(dst_path, mode="a", encoding="utf-8") as file:
            file.write(",".join(output) + "\n")
        logger.debug("SHA256 was %s.", output[2])


def write_json(data: Dict[str, Any], path: str) -> None:
    """
    Write a dictionary to a JSON file.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def read_json(path: str) -> Dict[str, Any]:
    """
    Read a JSON file (assumed to be a dictionary).
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        return {}


def calc_sha256(path: str, buffer_size: int = 65536) -> str:
    "Calculates the SHA256 of a file."
    algorithm = hashlib.sha256()
    with open(path, "rb") as file_in:
        while True:
            data = file_in.read(buffer_size)
            if not data:
                break
            algorithm.update(data)
    return algorithm.hexdigest()


def calc_md5(path: str, buffer_size: int = 65536) -> str:
    "Calculates the MD5 of a file."
    algorithm = hashlib.md5()
    with open(path, "rb") as file_in:
        while True:
            data = file_in.read(buffer_size)
            if not data:
                break
            algorithm.update(data)
    return algorithm.hexdigest()
