@ECHO OFF
call activate
python -m black .
python -m mypy src/tidynotes
python -m pylint src/tidynotes
PAUSE
