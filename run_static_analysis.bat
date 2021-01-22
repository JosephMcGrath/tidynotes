@ECHO OFF
call activate
python -m black src
python -m mypy src
python -m pylint src
PAUSE
