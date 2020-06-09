@echo off
set myBaseDir=%~dp0
set app=..\tasktracker.bat
echo ====================================
echo Running add test to setup db.
echo ====================================
call add.bat
echo ====================================
echo TEST - Edit existing task's name
set tstOptions=edit Task001 -n EditTask001
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Edit existing task description
set tstOptions=edit EditTask001 -d "Description for a task"
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----
