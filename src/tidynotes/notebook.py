import datetime
import glob
import json
import logging
import os
from typing import Dict, List, Union, Any

import jinja2
import pkg_resources

from .mardown_document import MarkdownPart


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
        for path in glob.glob(note_pattern, recursive=True):
            MarkdownPart.from_file(path)
        return [
            MarkdownPart.from_file(x) for x in glob.glob(note_pattern, recursive=True)
        ]

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
        self.notes = self.read_notes()
        for this_note in self.notes:
            this_note.to_file(this_note.meta[".file"]["path"])

    def extract_project(self, pattern: str) -> MarkdownPart:
        """Extract all entries for a project."""
        output = MarkdownPart(f"# {pattern}")
        self.notes = self.read_notes()
        for this_note in self.notes:
            for part in this_note.extract_parts(pattern):
                output.add_part(part)
                output.parts[-1].title = this_note.title
        return output

    def make_part_list(self) -> Dict[str, List[str]]:
        """Generate a list of projects and tasks in the notebook."""
        projects = set()
        tasks = set()
        for this_note in self.notes:
            projects.update([x.title for x in this_note.parts])
            for this_project in this_note.parts:
                tasks.update([x.title for x in this_project.parts])

        return {"projects": sorted(list(projects)), "tasks": sorted(list(tasks))}

    def _working_path(self, file_name):
        return os.path.join(self.root_path, self.working_dir, file_name)


def write_json(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(data)
