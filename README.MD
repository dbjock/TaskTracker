# TaskTracker
TaskTracker is a CLI python application for tracking and reporting time spend on a tasks.

## Requirements
- Python version 3.7, 3.8
- PyYAML==5.3.1

## Setup
### `log.conf`
Copy the log.conf.example file to log.conf for the logging configuration.

If you don't change anything in the `log.conf` file then create a `logs` directory relative to the app. You can change the location and log file names by editing the `log.conf` just look for `filename:` and change the value.

- The log.conf is YAML based.
- the loggers defined in the app are as follows:
    - `TaskTracker`
    - `taskdb`
    - `root`

## Usage

```
python tasktracker.py [-h] [-e] {add,edit,list,report,track}

optional arguments:
  -h, --help            show this help message and exit
  -e                    End trackingcommand options are found with tasktracker -h

-e is used to stop tracking the current trask
```

Further details of the command help can be found:
```
add -h
delete -h
edit -h
list -h
purge -h
report -h
track -h
```

## Changes
2.03
- Added ability to purge track detail records by days old or days old by task name.
- Enhance reporting to include task description and improvements on output.

2.02a
 - Bug Fix: Reporting on a task would cause an error

2.02
 - Ability to delete a task with confirmation required.

2.01
 - Report allows exporting, and reformated output.

2.00
 - Didn't exist in github yet.
