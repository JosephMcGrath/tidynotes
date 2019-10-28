import os
import jinja2

# TODO: Format dates to pass through to note generation,
# TODO: Render markdown to html,
# TODO: Log the hash of any files rendered,
# TODO: Accept command-line inputs,
# TODO: Replacements at the time of rendering,
# TODO: Heading management (project / task names),
# TODO: To-do list,


class notebook:
    def __init__(self, note_path, template_path):
        self.note_path = note_path
        self.template_path = template_path

        _ = jinja2.FileSystemLoader(self.template_path)
        self.env = jinja2.Environment(loader=_)

    def write(self, file_path: str, content: str):
        """Writes a string to a file."""
        with open(file_path, "w", encoding="utf-8") as f:
            return f.write(content)

    def make_note(self):
        template = self.env.get_template("note.md")
        output = template.render()
        return output

    def write_note(self):
        self.write(os.path.join(self.note_path, "Note.md"), self.make_note())


if __name__ == "__main__":
    book = notebook(
        note_path=os.path.join(os.getcwd(), "notes"),
        template_path=os.path.join(os.getcwd(), "templates"),
    )

    book.write_note()
