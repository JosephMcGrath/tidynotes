# Markdown Notebook

A script to generate a notebook in Markdown. The basic setup is designed around how I take digital notes but should be fairly hackable. I use it to make a single file per day that can then be merged into a single hmtl export.

Inside each note:

* There's a single level 1 heading that is the name of the note (generally the day it covers),
* Each project goes under a level 2 heading,
* Tasks within those projects have a level 3 heading,
* Level 4 & 5 headings are optional sub-divisions within those tasks,

The script is designed to be called from the command-line. It takes a directory passed as a positional argument and a number of flags:

* ```-m```/```--make_note``` generates a note for the current day,
* ```-s```/```--make_series``` generates notes for n days in the future,
* ```-d```/```--make_day``` generates notes a day specified as a text value,
* ```-i```/```--initialise_notebook``` generates a blank notebook in the directory,
* ```-r```/```--render_all``` merges all markdown files and renders them into a single html output,
* ```-c```/```--clean_headings``` runs a simple heading cleanup routine and runs user-set regex over all notes,
* ```-e```/```--extract_project``` extracts and renders the notes for a specific project,
* ```-a```/```--extract_all``` extracts and renders the notes for all projects,
