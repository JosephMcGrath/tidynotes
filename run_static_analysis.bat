@ECHO OFF
call %conda_activate%
black src
pylint src
PAUSE
