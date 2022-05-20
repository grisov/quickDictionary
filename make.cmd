@echo off
del /s /q addon\manifest.ini>NUL
del /s /q *.nvda-addon>NUL
call ..\scons -s
"quickDictionary-2.1.5.nvda-addon"
