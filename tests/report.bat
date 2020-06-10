@echo off
set myBaseDir=%~dp0
set app=..\tasktracker.bat
echo ====================================
echo Report testing - Required test db.
echo ====================================

echo TEST - report since 2000
set tstOptions=report 2000-01-01
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----