# Tidynotes

A script to generate a notebook in Markdown. The basic setup is designed around how I take digital notes but should be fairly hackable. I use it to make a single file per day that can then be merged into a single hmtl export or an export for each project I'm working on.

Inside each note:

* There's a single level 1 heading that is the name of the note (generally the day it covers),
* Each project goes under a level 2 heading,
* Tasks within those projects have a level 3 heading,
* Level 4 & 5 headings are optional sub-divisions within those tasks,

The script is designed to be called from the command-line. It takes a directory passed as a positional argument and a number of flags:

* ```-g```/```--generate_note``` generates a note for the current day,
* ```-s```/```--make_series``` generates notes for n days in the future,
* ```-i```/```--initialise_notebook``` generates a blank notebook in the directory,
* ```-r```/```--render_all``` merges all markdown files and renders them into a single html output,
* ```-c```/```--clean``` runs a simple heading cleanup routine and runs user-set regex over all notes,
* ```-e```/```--extract_project``` extracts and renders the notes for a specific project,
* ```-a```/```--extract_all``` extracts and renders the notes for all projects,

The script also allows for a few additional features (mainly during cleanup):

* Storing a list of all projects / tasks. This is mainly to allow corrections of misspellings etc.
* A list of regex corrections. The default set:
    * Standardises newlines between tasks,
    * Newline at the end of each file,
    * Homogenises quote marks (e.g. ’ to '),
