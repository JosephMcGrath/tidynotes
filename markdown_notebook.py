import os
import jinja2
import datetime
import markdown
import re

# TODO: Render markdown to html,
# TODO: Log the hash of any files rendered,
# TODO: Accept command-line inputs,
# TODO: Replacements at the time of rendering,
# TODO: Heading management (project / task names),
# TODO: To-do list,
# TODO: Use a config file in the notebook rather than pre-defined strings,
# TODO: Extract (& render) all entires under a single heading,


class notebook:
    def __init__(self, note_path, template_path, notebook_name="Test"):
        self.note_path = note_path
        self.template_path = template_path

        _ = jinja2.FileSystemLoader(self.template_path)
        self.env = jinja2.Environment(loader=_)

    def write(self, file_path: str, content: str):
        "Writes a string to a file."
        dst_dir = os.path.split(file_path)[0]
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        with open(file_path, "w", encoding="utf-8") as f:
            return f.write(content)

    def read(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return text

    def make_note(self, date=datetime.datetime.today()):
        template = self.env.get_template("note.md")
        output = template.render(dates=self.format_date(date))
        return output

    def write_note(self, date=datetime.datetime.today()):
        dates = self.format_date(date)
        self.write(
            os.path.join(self.note_path, dates["path"], dates["file"]),
            self.make_note(date),
        )

    def format_date(self, target_date):
        """Formats a date into useful predefined formats."""
        formats = {
            "title": "%Y-%m-%d (%A)",
            "file": "notes_%Y-%m-%d_%a.md",
            "path": "%Y/%m",
        }
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
        output = ["".join(x) for x in output]
        return output


if __name__ == "__main__":
    book = notebook(
        note_path=os.path.join(os.getcwd(), "notes"),
        template_path=os.path.join(os.getcwd(), "templates"),
    )

    book.write_note()
