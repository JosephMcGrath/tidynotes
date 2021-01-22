import datetime
import glob
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import jinja2
import pkg_resources

from .mardown_document import MarkdownPart

# TODO : Logging
# TODO : Regex note search
# TODO : Config management
# TODO : Dates in header as dates - YAML handles that


class Notebook:
    log_name = "Tidynotes"
    template_dir = "templates"
    note_dir = "notes"
    working_dir = "working"

    def __init__(self, notebook_dir: str) -> None:
        logger = self._make_logger()
        self.root_dir = os.path.abspath(notebook_dir)
        self.config: Dict[str, Union[str, int]] = self._read_config()

        _ = jinja2.FileSystemLoader(os.path.join(self.root_dir, self.template_dir))
        self.env = jinja2.Environment(loader=_)

        self.notes = self.read_notes()

        logging.info("Set up notebook in %s.", self.root_dir)

    @classmethod
    def initialise(cls, notebook_dir: str) -> "Notebook":
        template_list = {
            "config.json": "",
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
                continue

            os.makedirs(dst_dir, exist_ok=True)
            src_path = os.path.join("templates", template)
            raw = pkg_resources.resource_string(__name__, src_path)

            with open(dst_path, "wb") as file_out:
                raw = pkg_resources.resource_string(__name__, src_path)
                file_out.write(raw)

        return cls(notebook_dir)

    def read_notes(self) -> List[MarkdownPart]:
        """Read all notes from files."""
        note_pattern = os.path.join(self.root_dir, self.note_dir, "**", "*.md")
        notes = []
        for path in glob.glob(note_pattern, recursive=True):
            temp = MarkdownPart.from_file(path)
            temp.set_level(2)
            notes.append(temp)
        return notes

    def make_note(self, date=datetime.datetime.today(), force=False):
        """Generates and writes a note for the specified date."""
        # TODO : Notebook name in headers.
        logger = self._make_logger("Generation")
        logger.debug("Generating a note for %s.", date)

        dst_path = os.path.join(
            self.root_dir, self.note_dir, date.strftime(self.config["note_file_format"])
        )
        os.makedirs(os.path.split(dst_path)[0], exist_ok=True)
        if force or not os.path.exists(dst_path):
            template = self.env.get_template("note.md")
            output = MarkdownPart(template.render(date=date))
            output.meta["created"] = date.isoformat()
            output.to_file(dst_path)
        else:
            logger.debug("Note already exists - skipping.")
        logger.debug("Finished writing note.")

    def _make_logger(self, sub_log=None) -> logging.Logger:
        "Get the logger for the notebook, with an optional sub-log name."
        if isinstance(sub_log, str):
            log_name = f"{self.log_name}.{sub_log}"
        else:
            log_name = self.log_name
        return logging.getLogger(log_name)

    def _read_config(self) -> None:
        logger = self._make_logger()
        config_path = os.path.join(self.root_dir, "config.json")
        logger.debug("Reading config from %s.", config_path)

        if not os.path.exists(config_path):
            message = (
                "Config path doesn't exist. Maybe it needs to be initialised first?"
                f" The path given was {config_path}"
            )
            logger.error(message)
            raise RuntimeError(message)

        with open(config_path, encoding="utf-8") as file_in:
            config = json.load(file_in)
        logger.debug("Finished reading config.")
        return config

    def clean(self) -> None:
        """General cleanup operations on the notebook."""
        self.update_projects_and_tasks()
        self.text_corrections()
        for this_note in self.notes:
            temp_level = this_note.level
            this_note.set_level(1)
            this_note.to_file(this_note.meta[".file"]["path"])
            this_note.set_level(temp_level)

    def extract_project(self, pattern: str) -> List[MarkdownPart]:
        """Extract all entries for a project."""
        output = []
        for this_note in self.notes:
            for part in this_note.extract_parts(pattern):
                part.title = this_note.title
                part.set_level(2)
                output.append(part)
        return output

    def update_projects_and_tasks(self):
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

    def text_corrections(self):
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

    def _working_path(self, file_name) -> str:
        return os.path.join(self.root_dir, self.working_dir, file_name)

    def render_full(self, dst_path: str) -> None:
        self._render(
            notes=self.notes, title=self.config["notebook_name"], dst_path=dst_path
        )

    def render_project(self, project_name: str, dst_path: str) -> None:
        self._render(
            notes=self.extract_project(project_name),
            title=project_name,
            dst_path=dst_path,
        )

    def _render(self, notes: List[MarkdownPart], title: str, dst_path: str) -> None:
        output = self.env.get_template("page.html").render(
            **self.config, notes=notes, title=title
        )

        with open(dst_path, "w", encoding="utf-8") as file:
            file.write(output)


def write_json(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def read_json(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        return {}
