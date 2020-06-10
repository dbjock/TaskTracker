@echo off
set myBaseDir=%~dp0
set app=..\tasktracker.bat

echo TEST - List task in database
set tstOptions=list
echo command: %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----
