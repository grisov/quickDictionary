@echo off
del /s /q addon\manifest.ini>NUL
del /s /q *.nvda-addon>NUL
call ..\scons -s
"quickDictionary-1.0.nvda-addon"
