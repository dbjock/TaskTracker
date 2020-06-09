@echo off
set myBaseDir=%~dp0
set app=..\tasktracker.bat
echo ====================================
echo Running add test to setup db.
echo ====================================
call add.bat
echo ====================================
echo TEST - Delete an existing task
set tstOptions=delete Task001
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Delete NON existing task
set tstOptions=delete WhatTask
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Delete task with quotes
set tstOptions=delete "Task Test 002"
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----
