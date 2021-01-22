"""
General markdown document control.
"""

import copy
import os
import re
from typing import Any, Dict, List, Optional

import jinja2
import markdown
import yaml


class MarkdownPart:
    # TODO : Support title-less documents (limited support)
    """
    A part of a markdown document.

    Has several mandatory attributes:

    * title - the name of the document / section.
    * body - the text of the section.
    * parts - sub-sections (also MarkdownParts) for any sub-headings.
    * metadata - any metadata for the object (stored in a YAML header).
    * level - the markdown level of the section (with 0 being used for Pandoc PDFs).

    And one optional attribute:

    * file - The path that the document came from (if applicable).
    """
    renderer = markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "admonition"]
    )
    env = jinja2.Environment(loader=jinja2.PackageLoader("tidynotes"))

    def __init__(self, text: str) -> None:
        self.raw = text
        self.level = 0
        self.file: Optional[str] = None

        self.title: str = ""
        self.body: str = ""
        self.parts: List[MarkdownPart] = []
        self.meta: Dict[str, Any] = {}

        self._parse_raw(text)

    @classmethod
    def from_file(cls, path: str, encoding: str = "utf-8") -> "MarkdownPart":
        """
        Load a markdown document from a text file at the specified path.
        """
        with open(path, encoding=encoding) as file:
            text = file.read()
        doc = cls(text)

        file_name = os.path.split(path)[1]
        file_name = os.path.splitext(file_name)[0]
        doc.file = file_name
        doc.meta[".file"] = {
            "path": path,
            "mtime": os.stat(path).st_mtime,
            "name": file_name,
        }

        return doc

    def to_file(self, path: str, encoding: str = "utf-8") -> None:
        """
        Writes the document to a text file at the specified path.
        """

        output = self.combine()

        if not output:
            return

        if os.path.exists(path):
            with open(path, "r", encoding=encoding) as file:
                existing = file.read()
            if existing == output:
                return

        with open(path, "w", encoding=encoding) as file:
            file.write(output)

    def combine(self, metadata: bool = True) -> str:
        """
        Recombine the document and its parts into a markdown string.
        """
        parts = []
        if metadata and self.meta:
            useable_meta = {x: y for x, y in self.meta.items() if x not in [".file"]}
            useable_meta["title"] = self.title
            meta_block = "\n".join(["---", yaml.dump(useable_meta).strip(), "---", ""])
            parts.append(meta_block)
        if self.level > 0:
            title = "#" * self.level + " " + self.title + "\n"
        else:
            title = ""
        body = "\n".join([title, self.body.strip("\n"), ""]).strip("\n") + "\n"
        if self.level == 2:
            body = "\n" * 2 + body
        elif self.level == 3:
            body = "\n" + body
        parts.append(body)
        if self.parts:
            parts.append("\n".join([x.combine(metadata=False) for x in self.parts]))
            if not self.body.strip():
                parts[-1] = parts[-1].lstrip("\n")

        return "\n".join(parts)

    def drop_parts(self, pattern: str) -> None:
        """
        Drop any parts that have a title matching the provided regex.
        """
        self.parts = [x for x in self.parts if not re.match(pattern, x.title)]

    def copy(self) -> "MarkdownPart":
        """
        Create a copy of the document and all its parts.
        """
        return copy.deepcopy(self)

    def extract_parts(self, pattern: str) -> List["MarkdownPart"]:
        """
        Extract any parts of the document that have a title matching the provided regex.
        """
        # TODO : Non-regex version & depth limit.
        output = []
        for part in self.parts:
            if re.match(pattern, part.title):
                output.append(part.copy())
            output.extend(part.extract_parts(pattern))
        return output

    def is_stub(self) -> bool:
        """
        Checks if the note is a stub (no body text and no parts).
        """
        return not self.body.strip() and len(self.parts) == 0

    def make_replacement(
        self, pattern: str, replacement: str, regex: bool = True
    ) -> None:
        """
        Replace any text in the body patching `pattern` with `replacement`.
        If `regex` is true then re.sub is used.
        """
        if regex:
            self.body = re.sub(pattern, replacement, self.body)
        else:
            self.body = self.body.replace(pattern, replacement)
        for part in self.parts:
            part.make_replacement(pattern, replacement, regex=regex)

    def replace_title(
        self, replacements: Dict[str, str], level: Optional[int] = None
    ) -> None:
        """
        Replace the title of the document or its children using a dictionary map.
        """
        if level is None or level == self.level:
            self.title = replacements.get(self.title, self.title)
        if level == self.level:
            return

        for part in self.parts:
            part.replace_title(replacements=replacements, level=level)

    def get_links(self) -> List[str]:
        """
        Get any wikilink-style links from the document or its children.
        """
        links = re.findall(r"\[\[([^\]]*)\]\]", self.body)
        for part in self.parts:
            links.extend(part.get_links())
        return links

    def get_images(self) -> List[str]:
        """
        Get any wikilink-style links from the document or its children.
        """
        images = re.findall(r"\!\[([^\]]*)\]\(([^\)]*)\)", self.body)
        images = [x[1] for x in images]
        for part in self.parts:
            images.extend(part.get_images())
        return images

    def add_part(self, new_part: "MarkdownPart") -> None:
        """
        Add a copy of the provided part as a sub-heading.
        """
        new_part = new_part.copy()
        new_part.set_level(self.level + 1)
        self.parts.append(new_part)

    def html(self) -> str:
        """
        Render this document as a a chunk of HTML.
        """
        return self.env.get_template("document.html").render(document=self)

    def _body_html(self) -> str:
        return self.renderer.convert(self.combine(metadata=False))

    def _parse_raw(self, text: str) -> None:
        """
        Parse raw markdown into its component parts.
        """
        # TODO : Split this function up.
        heading_pattern = re.compile(r"^(#+) (.*)$")
        lines = text.split("\n")
        level = -1
        title = ""
        line_no = -1

        # Parse metadata
        if lines[0].startswith("---"):
            meta_block = []
            for line_no, line in enumerate(lines):
                if line.startswith("---"):
                    if line_no > 0:
                        break
                else:
                    meta_block.append(line)
            self.meta = {**self.meta, **yaml.safe_load("\n".join(meta_block))}
            if "title" in self.meta:
                title = self.meta["title"]
                level = 0
                lines = lines[line_no + 1 :]

        # Get header
        for line_no, line in enumerate(lines):
            if not re.match(heading_pattern, line):
                continue

            temp, first_heading = re.findall(heading_pattern, line)[0]

            if not title or first_heading == title:
                title = first_heading
                level = len(temp)
            lines = lines[line_no + 1 :]
            break
        if not title:
            raise ValueError("Couldn't find a title in the document.")

        child_pattern = re.compile(f"^({'#' * (level + 1)}) (.*)$")

        # Parse main text
        body: List[str] = []
        for line_no, line in enumerate(lines):
            if re.match(child_pattern, line):
                break
            body.append(line)
        lines = lines[line_no:]

        # Parse children
        current_child: List[str] = []
        children: List[MarkdownPart] = []
        for line_no, line in enumerate(lines):
            if not re.match(child_pattern, line):
                current_child.append(line)
            else:
                temp = "\n".join(current_child)
                if temp.strip():
                    children.append(MarkdownPart(temp))
                current_child = [line]
        if current_child and re.match(child_pattern, current_child[0]):
            temp = "\n".join(current_child)
            if temp.strip():
                children.append(MarkdownPart(temp))

        self.title = title
        self.body = "\n".join(body).strip("\n") + "\n"
        self.parts = children
        self.set_level(level)

    def set_level(self, level: int) -> None:
        """
        Set the level of a document part.
        Its children parts are set to one level higher (recursively).
        """
        self.level = level
        for part in self.parts:
            part.set_level(level + 1)

    def __repr__(self) -> str:
        return f"<MarkdownPart, title = {self.title}, level = {self.level}>"

    __str__ = __repr__
