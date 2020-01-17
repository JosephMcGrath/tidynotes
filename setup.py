import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="tidynotes",
    version="20.01.03",
    description="A simple digital notebook using Markdown.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/JosephMcGrath/tidynotes",
    author="Joe McGrath",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=["tidynotes"],
    include_package_data=True,
    install_requires=[
        "argparse",
        "datetime",
        "collections",
        "hashlib",
        "jinja2",
        "json",
        "markdown",
        "os",
        "re",
        "shutil",
    ],
    entry_points={"console_scripts": ["tidynotes=tidynotes.__main__:main"]},
)
