# Required base modules
from pathlib import Path
import logging
import logging.config
import yaml
from datetime import datetime, timezone, timedelta
import argparse
import sys
import csv

# App custom modules
from tasktracker import taskdb

APP_VER = "2.03"
logger = logging.getLogger("TaskTracker")

with open("log.conf", 'rt') as f:
    config = yaml.safe_load(f.read())

logging.config.dictConfig(config)


def listTask(dbConn):
    """List all tasks to console, and indicate what tasks are active
    PARMS:
    dbConn : Database connection object
    nothing is return. Just displays to console
    """
    tasks = taskdb.getTasks(dbConn)
    logger.info(f"Total Tasks: {len(tasks)}")
    print("Tasks: Task Name (Task Description)")
    if len(tasks) == 0:  # No tasks in database
        print("\tNone")
    else:
        for task in tasks:
            if task[2]:  # there is a task desc
                description = f"({task[2]})"
            else:
                description = ""
            print(f"\t{task[1]} {description}")

    activeTask = taskdb.getActiveTask(dbConn)
    print("Active Task:")
    if len(activeTask) == 0:  # no Active task
        logger.info(f"No task active")
        print("\tNone")
    else:
        for aTask in activeTask:
            aTaskID = aTask[0]
            aTaskName = aTask[1]
            aTrackID = aTask[2]
            aTaskDesc = aTask[3]
            logger.debug(f"aTask = {aTask}")
            logger.debug(
                f"aTaskID = {aTask[0]} aTaskName = '{aTask[1]}' aTrackID = {aTask[2]} aTaskDesc = '{aTask[3]}'")
            msg = f"\t{aTaskName} ({aTaskDesc})"
            print(msg)


def addingTask(dbConn, taskName="", taskDesc=""):
    """Add a Task to the database"""
    logger.info(
        f"Add task '{taskName}' to database. Description: '{taskDesc}'")
    if taskdb.addTask(dbConn, taskName=taskName, taskDesc=taskDesc):  # Succesfully added
        msg = f"Task '{taskName}' added"
    else:
        msg = f"Task '{taskName}' already exists"

    logger.info(msg)
    print(msg)


def deleteTask(dbConn, taskName):
    """Delete a task from database, and all of its tracking"""
    # Get the taskID for the taskname
    taskInfo = taskdb.getTaskID(dbConn, taskName)
    logger.debug(f"taskInfo = {taskInfo}")
    if taskInfo == None:  # No task found
        msg = f"'{taskName}' not found"
        logger.info(msg)
        print(msg)
        return

    # Get confirmation
    confirm = input("  !! Type 'CONFIRM' to delete : ")
    if confirm != 'CONFIRM':
        msg = f"Task '{taskInfo[1]}' not deleted. User did not confirm to delete."
        logger.info(msg)
        print(msg)
        return

    # Getter done
    result = taskdb.delTask(dbConn, taskID=taskInfo[0])
    if result:
        msg = f"Task '{taskInfo[1]}' deleted"
    else:
        msg = f"Task '{taskInfo[1]}' not deleted see logs"

    logger.info(msg)
    print(msg)
    return


def editTask(dbConn, orgTaskName, newTaskName=None, newTaskDesc=None):
    """Editing a task"""
    # Validation:
    if newTaskName == '' or newTaskName == "''":
        msg = "Invalid request: Please do not try to clear the task name."
        logger.info(msg)
        print(msg)
        return
    elif newTaskName == None and newTaskDesc == None:
        msg = "Invalid request: Not sure what you want to change?"
        logger.info(msg)
        print(msg)
        return

    # Get the taskID for the taskname
    taskInfo = taskdb.getTaskID(dbConn, orgTaskName)
    logger.debug(f"taskInfo = {taskInfo}")
    if taskInfo == None:  # No task found
        msg = f"'{orgTaskName}' not found"
        logger.info(msg)
        print(msg)
        return

    # Getter done
    result = taskdb.changeTask(
        dbConn, taskID=taskInfo[0], newName=newTaskName, newDesc=newTaskDesc)
    if result:
        msg = "Task Update"
    else:
        msg = f"'{orgTaskName}' not update. Task name already exists"

    logger.info(msg)
    print(msg)
    return


def deactivateTasks(dbConn, utc_dt, silent=False):
    """end tracking on active task(s)

    PARM:
    dbConn : DB connection object
    utc_dt : UTC time value for endtime on active task(s)
    silent : True - no report of tasks not found. False - report if tasks not found
    """
    activeTask = taskdb.getActiveTask(dbConn)
    if len(activeTask) == 0:  # no Active task
        logger.info(f"No task active")
        if not silent:
            print("No active tasks found to end tracking on")
    else:
        for aTask in activeTask:
            aTaskID = aTask[0]
            aTaskName = aTask[1]
            aTrackID = aTask[2]
            logger.info(
                f"Deactivate TaskID: {aTaskID} TaskName: '{aTaskName}' TrackID: {aTrackID}")
            taskdb.setTaskTrack(dbConn, aTaskID, utc_dt, trackID=aTrackID)
            localNow = utc_to_local(utc_dt)
            print(
                f"'{aTaskName}' tracking ended {localNow.strftime('%Y-%m-%d %H:%M:%S %z')}")
    logger.debug("End track on active tasks complete")


def trackTask(dbConn, taskName):
    """Start time track for task name, and end tracking on active task."""
    # What is current utc time
    utcNow = local_to_utc(datetime.now())
    localNow = utc_to_local(utcNow)

    # end tracking on active task(s)
    deactivateTasks(dbConn, utcNow, silent=True)
    # Does the task exist?
    taskRows = taskdb.getTaskID(dbConn, taskName)
    if taskRows:
        taskID = taskRows[0]
        taskdb.setTaskTrack(dbConn, taskID, utcNow)
        print(
            f"'{taskRows[1]}' tracking started {localNow.strftime('%Y-%m-%d %H:%M:%S %z')}")
        logger.debug(
            f"'{taskRows[1]}' tracking local: {localNow} DBTime: {utcNow}")
    else:  # Nothing found
        logger.debug("task name not found")
        print(f"'{taskName}' - NOT FOUND")


def reportHours(dbConn, startDate, endDate, taskName=None, exportFile=None):
    """Report hourse worked
    PARMS:
    startDate : datetime - Start datetime for report.
    endDate : datetime - End datetime for report (This date will be included).
    taskName : (optional) TaskName to report
    exportFile : Export file name to output csv data

    RETURN - nothing
    """
    logger.debug(
        f"Getting reporting for startDate: {startDate}, endDate: {endDate}, taskName: {taskName}, exportFile: {exportFile}")
    startUTC = local_to_utc(startDate)
    # ---------------------
    # Validation steps
    # ---------------------
    # startUTC must be less than now
    if startDate >= datetime.now():  # startdate not valid
        logger.info(f"startdate {startDate.strftime('%Y-%m-%d')} >= now")
        print(f"startdate must be less than now")
        sys.exit()

    # if endDate, then make sure it's > than startdate
    if endDate:  # must be > than startdate
        lastUTC = local_to_utc(endDate)
        logger.debug(f"converted LastUTC from endDate")
        if endDate < startDate:
            msg = f"lastdate {endDate.strftime('%Y-%m-%d')} must be greater than startdate {startDate.strftime('%Y-%m-%d')}"
            logger.info(msg)
            print(msg)
            sys.exit()
    else:  # make enddate now
        logger.debug(f"endDate not provided. Converted LastUTC from now")
        lastUTC = local_to_utc(datetime.now())

    # Creating TZ aware vars
    lastLocal = utc_to_local(lastUTC)  # lastLocal is TZ aware now
    startLocal = utc_to_local(startUTC)  # startLocal is TZ aware now
    logger.debug(
        f"converted startDate -> startLocal: {startLocal.isoformat()}")
    logger.debug(f"converted startDate -> startUTC: {startUTC.isoformat()}")
    logger.debug(f"converted lastdate -> lastLocal: {lastLocal.isoformat()}")
    logger.debug(f"converted lastdate -> lastUTC: {lastUTC.isoformat()}")

    # Get taskname correct case from database (and make sure it exists)
    if taskName:  # Get official task name from database
        taskRow = taskdb.getTaskID(dbConn, taskName)
        if taskRow:  # Task found
            taskName = taskRow[1]
            logger.debug(f"converted taskName -> {taskName}")
            preMsg = f"Reporting on task: '{taskName}'"
        else:  # Task not found in database
            logger.info(
                f"Not able to report on task '{taskName}' - it was not found")
            print(f"Not able to find task '{taskName}'")
            return
    else:
        preMsg = f"Reporting all tasks"

    logger.info(
        f"Reporting for startUTC: {startUTC.isoformat()}, lastUTC: {lastUTC.isoformat()}, taskName: {taskName}, exportFile: {exportFile}")
    print(
        f"{preMsg} from {startLocal.strftime('%Y-%m-%d')} to {lastLocal.strftime('%Y-%m-%d')}")
    # Fetch report rows from database
    rptRows = taskdb.rptHours(
        dbConn, taskName=taskName, startDateUTC=startUTC, endDateUTC=lastUTC)
    logger.debug(f"Rows returned: {len(rptRows)}")

    if rptRows:  # Have Hours to report
        # Find Max len of taskname;
        tasklen = 0
        for row in rptRows:  # Get max taskname width
            if len(row[1]) > tasklen:
                tasklen = len(row[1])
        # Print to screen
        for row in rptRows:
            rptDate = row[0]
            taskName = row[1]
            workedStr = "{:.1f}".format(row[2]) + " Hours"
            if row[3]:
                taskDesc = f"({row[3]})"
            else:
                taskDesc = ""
            print(f"\t{rptDate} {taskName:{tasklen}} {workedStr} {taskDesc}")

        if exportFile:  # Export report data to file.
            xpath = Path(exportFile)
            xpath.parent.mkdir(parents=True, exist_ok=True)
            _rptExport(rptRows, exportFile)
            print(f"Reported exported to : {exportFile}")

    else:
        logger.info(f"No work hours to report")
        print("No work hours to report")


def utc_to_local(utc_dt):
    """ converts utc time to local time

    PARMS:
    utc_dt : UTC timedate object that is TZ aware

    Returns : timdate object that is TZ aware
    """
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def local_to_utc(local_dt):
    """ Converts local naive time to UTC

    PARMS:
    local_dt : datetime object that is TZ naive

    Returns : UTC time TZ aware
    """
    return local_dt.replace(tzinfo=None).astimezone(tz=timezone.utc)


def _rptExport(rptRows, fileName):
    """Writes to csv file repRows
    PARMS:
    rptRows : list
    fileName : csv path and fileName
    """
    logger.info(f"Exporting report data to {fileName}")
    with open(fileName, mode='w', newline='\n') as csvFile:
        row_writer = csv.writer(csvFile, dialect='excel')
        row_writer.writerow(["Report Date", "Task", "Hours Worked"])
        for row in rptRows:
            rptDate = row[0]
            taskName = row[1]
            workedStr = "{:.1f}".format(row[2])
            if row[3]:
                taskDesc = f"({row[3]})"
            else:
                taskDesc = ""
            row_writer.writerow([rptDate, taskName, workedStr, taskDesc])


def main(parser):
    # Ensure path to database exists.
    dbFile = "data/tasktracking.db"
    path = Path(dbFile)
    path.parent.mkdir(parents=True, exist_ok=True)
    trackingDB = taskdb.create_connection(dbFile)
    args = parser.parse_args()
    logger.debug(f"args is {args}")
    if args.e:  # End tracking
        logger.info("option to end task tracking")
        utcNow = local_to_utc(datetime.now())
        deactivateTasks(trackingDB, utcNow)

    if args.command == 'list':
        listTask(trackingDB)
    elif args.command == 'track':
        logger.info(f"Option tracking task: {args.taskname}")
        trackTask(trackingDB, args.taskname)
    elif args.command == 'report':
        logger.info(f"Reporting command")
        reportHours(trackingDB, args.startdate, args.lastdate,
                    taskName=args.taskName, exportFile=args.exportfile)
    elif args.command == 'delete':
        logger.info(f"Deleting task '{args.taskname}'")
        deleteTask(trackingDB, taskName=args.taskname)
    elif args.command == 'add':
        if args.taskdesc:
            taskdesc = args.taskdesc
        else:
            taskdesc = ""
        logger.info(
            f"Option Adding task '{args.taskname}', Desc: '{taskdesc}' ")
        addingTask(trackingDB, taskName=args.taskname, taskDesc=taskdesc)
    elif args.command == 'edit':
        logger.info(f"Option Edit task '{args.taskname}'")
        editTask(trackingDB, orgTaskName=args.taskname,
                 newTaskName=args.newName, newTaskDesc=args.newDesc)


if __name__ == '__main__':
    logger.info("======= START ======= ")
    msg = f"Task Tracker version: {APP_VER}"
    logger.info(msg)
    print(msg)

    parser = argparse.ArgumentParser(description="Task Tracking app")
    parser.add_argument('-e', help='End tracking', action='store_true')

    commandSubparser = parser.add_subparsers(
        title="Commands", dest='command')

    # Add command for adding a task
    addTask_parser = commandSubparser.add_parser('add', help="Add a task")
    addTask_parser.add_argument(
        'taskname', help="Name of the task to edit", type=str)
    addTaskGroup = addTask_parser.add_argument_group(
        "Add Command (Adding a Task)")
    addTaskGroup.add_argument(
        '-d', '--desc', help='Description of task',  metavar='taskdesc', type=str, dest='taskdesc')

    # Delete command (Deleting a task)
    delTask_parser = commandSubparser.add_parser(
        'delete', help='Delete a task')
    delTaskGroup = delTask_parser.add_argument_group(
        "Delete Command (Deleting a Task")
    delTaskGroup.add_argument(
        'taskname', help="Name of task to delete", type=str)

    # Edit command to edit a task
    editTask_parser = commandSubparser.add_parser('edit', help="Edit a task")
    editTask_parser.add_argument(
        'taskname', help="Name of the task to edit", type=str)
    editTaskGroup = editTask_parser.add_argument_group(
        'Edit Command (Editing a Task)')
    editTaskGroup.add_argument(
        '-n', '--newName', help='New name for task', metavar='new_name', type=str, dest='newName')
    editTaskGroup.add_argument(
        '-d', '--newDesc', help='New description task',  metavar='new_desc', type=str, dest='newDesc')

    # List command to list task(s) TODO: Want this to work like list WSSEMD*
    list_parser = commandSubparser.add_parser('list', help="List all tasks")

    # Report command to report task(s) TODO: Want this to work like list WSSEMD*
    report_parser = commandSubparser.add_parser(
        'report', help="Reporting working hours")
    reportTaskGroup = report_parser.add_argument_group(
        "Report Command (Reporting working hours)")
    report_parser.add_argument(
        'startdate', help='Start Date to report on (YYYY-MM-DD)', type=datetime.fromisoformat)
    reportTaskGroup.add_argument(
        '-t', '--task', help='Task name to report', metavar='taskname', type=str, dest='taskName')
    reportTaskGroup.add_argument('-l', '--lastdate', help='Last date for report (YYYY-MM-DD)',
                                 metavar='lastdate', type=datetime.fromisoformat, dest='lastdate')
    reportTaskGroup.add_argument('-E', '--Export', help='Export to a csv file report',
                                 metavar='exportfile', type=str, dest='exportfile')

    # Track command to track a task
    track_parser = commandSubparser.add_parser('track', help='Track a task')
    track_parser.add_argument(
        'taskname', help="Name of the task to track", type=str)

    args = parser.parse_args()
    main(parser)
