import os
import jinja2
import datetime

# TODO: Render markdown to html,
# TODO: Log the hash of any files rendered,
# TODO: Accept command-line inputs,
# TODO: Replacements at the time of rendering,
# TODO: Heading management (project / task names),
# TODO: To-do list,
# TODO: Use a config file in the notebook rather than pre-defined strings,


class notebook:
    def __init__(self, note_path, template_path):
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
        return {x : target_date.strftime(formats[x]) for x in formats}


if __name__ == "__main__":
    book = notebook(
        note_path=os.path.join(os.getcwd(), "notes"),
        template_path=os.path.join(os.getcwd(), "templates"),
    )

    book.write_note()
