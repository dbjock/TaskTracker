@echo off
set myBaseDir=%~dp0
set app=..\tasktracker.bat
set taskDB=..\data\tasktracking.db
REM -- Delete database if it exsists
echo Existing Database Check
if exist %taskDB% (
    echo -- Existing database deleted
    del %taskDB%
) ELSE (
    echo -- No existing database found.
)
echo TEST - Adding task no description
set tstOptions=add Task001
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Adding task with description
set tstOptions=add Task002 -d "I am a description"
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Adding task with quotes and desc with quotes
set tstOptions=add "Task Test 002" -d "I am a description"
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----

echo TEST - Adding duplicate task.
set tstOptions=add Task001
echo ^> %app% %tstOptions%
call %app% %tstOptions%
cd %myBaseDir%
echo ----