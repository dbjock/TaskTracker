import logging
import datetime
import sqlite3
import sys

logger = logging.getLogger('taskdb')


def create_connection(dbFile):
    """Create a Sqlite3 datbase connection to dbfile

    Args:
      dbfile : database file to connect
    Returns:
      Sqlite3 connection object or None
    """
    logger.debug(f"dbfile = {dbFile}")
    if dbFile is None or dbFile == "":
        logger.critical(f"This is a value error", exc_info=True)
        raise ValueError("dbFile must contain a value")
    try:
        conn = sqlite3.connect(dbFile)
        cur = conn.cursor()
        # Turning on foreign_key enforcement
        cur.execute("PRAGMA foreign_keys = ON")

        logger.debug(f"DB Connection successful to : {dbFile}")
        logger.debug(f"sqlite3 version {sqlite3.version}")
    except Exception as err:
        logger.critical(f"Error:  {err}", exc_info=True)
        sys.exit()

    # Check required database objects and if missing create.
    sql = "SELECT name FROM sqlite_master WHERE name='task'"
    c = conn.cursor()
    c.execute(sql)
    if c.fetchone() is None:  # Creating task table
        logger.info(f"Creating task table")
        createSql = """CREATE TABLE task (
        id   INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        name TEXT UNIQUE NOT NULL COLLATE NOCASE,
        [desc] TEXT)"""
        _exeSql(conn, createSql)

    sql = "SELECT name FROM sqlite_master WHERE name='tracking'"
    c = conn.cursor()
    c.execute(sql)
    if c.fetchone() is None:  # Creating tracking table
        logger.info(f"Creating tracking table")
        createSql = """CREATE TABLE tracking (
        id      INTEGER  PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        task_id INTEGER  REFERENCES task (id) ON DELETE CASCADE
                                        ON UPDATE CASCADE,
        started DATETIME UNIQUE NOT NULL,
        ended   DATETIME)"""
        _exeSql(conn, createSql)

    sql = "SELECT name FROM sqlite_master WHERE name='v_hours_wrked_detail'"
    c = conn.cursor()
    c.execute(sql)
    if c.fetchone() is None:  # Create the v_hours_wrked_detail view
        logger.info(f"Creating v_hours_wrked_detail")
        createSql = """CREATE VIEW v_hours_wrked_detail AS
        SELECT task.id AS task_id,
        task.name AS task_name,
        track.id AS track_id,
        track.started,
        track.ended,
        (julianday(track.ended) - julianday(track.started) ) * 24 AS Hours_worked
        FROM task
        JOIN
        tracking AS track ON task.id = track.task_id
        WHERE NOT track.ended IS NULL
        ORDER BY started"""
        _exeSql(conn, createSql)

    logger.info("Database Connection created")
    return conn


def _exeSql(dbConn, exeSql):
    """Executes exeSql.

    Args:
      dbConn    : database connection obj
      createSql : Create table sql statment
    Returns:
      True if successfull
    """
    logger.debug(f"executing sql: {exeSql}")
    try:
        dbCursor = dbConn.cursor()
        dbCursor.execute(exeSql)
        dbConn.commit()
        logger.debug(f"sql executed successfull")
        return True
    except Exception as err:
        logger.critical(f"Error:  {err}", exc_info=True)
        sys.exit()


def getTasks(dbConn):
    """Gets a list of tasks

    Args:
      dbConn : database connection obj

    Returns:
      list (TaskID, TaskName, TaskDesc)"""

    logger.info("Getting list of tasks")
    sql = "SELECT task.id, task.name, task.desc from TASK ORDER by task.name"
    logger.debug(f"SQL: {sql}")
    try:
        cursor = dbConn.cursor()
        cursor.execute(sql)
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    rows = cursor.fetchall()
    logger.info(f"rows fetched: {len(rows)}")
    return rows


def getActiveTask(dbConn):
    """Get a list of Active Tasks

    Args:
      dbConn : database connection obj

    Returns:
      list (TaskID, TaskName, Tracking_id, TaskDesc)"""

    logger.info(f"Getting List of Active Tasks")
    sql = """SELECT task.id as taskID, name as Task_name, tracking.id as Tracking_id, task.desc as Task_Desc
    FROM task
    JOIN tracking ON task.id = tracking.task_id
    WHERE tracking.ended = '' OR tracking.ended IS NULL
    ORDER BY task.name"""
    logger.debug(f"SQL: {sql}")
    try:
        cursor = dbConn.cursor()
        cursor.execute(sql)
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    rows = cursor.fetchall()
    logger.info(f"rows fetched: {len(rows)}")
    return rows


def addTask(dbConn, taskName="", taskDesc=""):
    """Add a Task to database

    Args:
      dbConn : database connection obj
      taskName : str name of the task (case insensitve)
      taskDesc : str description of the task

    Returns:
      True/False (Assumption False is due to taskName not unique)"""
    logger.info(f"attempt to add task name: {taskName}")
    theVals = (taskName, taskDesc)
    sql = "INSERT into task (name, desc) VALUES(?,?)"
    logger.debug(f"SQL: {sql}")
    logger.debug(f"theVals: {theVals}")
    try:
        dbCursor = dbConn.cursor()
        dbCursor.execute(sql, theVals)
        dbConn.commit()
    except sqlite3.IntegrityError as err:
        # UNIQUE constraint failed
        logger.info(f"Integrity Error={err}.")
        return False
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    logger.info("task added")
    return True


def changeTask(dbConn, taskID, newName=None, newDesc=None):
    """Change a task's name and/or description

    Args:
      dbConn   : database connection obj
      taskID   : Unique ID for the task to be changed
      newName  : str new name of the task (case insensitve)
      newDesc  : str new desc of the task (optional)

    Returns:
      True/False
      False = did not update. Assumption the newName is not unique
    """
    logger.debug(f"taskID = {taskID}, newName={newName}, newDesc={newDesc}")
    theVals = {'taskID': taskID, 'newName': newName, 'newDesc': newDesc}
    setSQL = "SET "
    whereSQL = "WHERE id = :taskID"
    nNameSet = "name = :newName"
    nDescSet = "desc = :newDesc"
    if newName != None and newDesc == None:
        setSQL = "SET " + nNameSet + " "
    if newName != None and newDesc != None:
        setSQL = "SET " + nNameSet + "," + nDescSet + " "
    if newName == None and newDesc != None:
        setSQL = "SET " + nDescSet + " "

    sql = "UPDATE task " + setSQL + whereSQL
    logger.debug(f"SQL: {sql}")
    logger.debug(f"theVals: {theVals}")
    try:
        dbCursor = dbConn.cursor()
        dbCursor.execute(sql, theVals)
        dbConn.commit()
    except sqlite3.IntegrityError as err:
        # UNIQUE constraint failed
        logger.debug(f"Integrity Error={err}.")
        return False
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    return True


def setTaskTrack(dbConn, taskID, timeValue, trackID=None):
    """Start or end tracking for a Task

    Args:
      dbConn: database connection obj
      taskID: Unique ID for the task that is going to be tracked
      timeValue: The UTC time value for starting/ending
      trackID: If provided timeValue is the endtime.
                If not provided new trackID record, with timeValue as starttime.

    Returns:
      True/False (True worked, False did not work)
    """
    if trackID:  # trackID has been provided
        logger.info(
            f"UPDATE trackingID: {trackID} for taskID {taskID} endtime {f'{timeValue}'}.")
        theVals = (timeValue, trackID)
        sql = "UPDATE tracking SET ended = ? WHERE id = ?"
    else:
        logger.info(
            f"Creating trackingID: for taskID {taskID}, startime {f'{timeValue}'}")
        theVals = (taskID, timeValue)
        sql = "INSERT into tracking (task_id, started) VALUES(?,?)"
    logger.debug(f"SQL: {sql}")
    logger.debug(f"Values: {theVals}")
    try:
        dbCursor = dbConn.cursor()
        dbCursor.execute(sql, theVals)
        dbConn.commit()
    except sqlite3.IntegrityError as err:
        # UNIQUE constraint failed
        logger.debug(f"Integrity Error={err}.")
        return False
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    logger.debug("tracking update")
    return True


def delTask(dbConn, taskID):
    """Delete a Task from the database

    Args:
      dbConn   : database connection obj
      taskID   : Unique ID of task to be deleted.

    Returns:
      True/False
      False = Did not get deleted
    """
    pass
    logger.info(f"Deleting taskid {taskID}")
    theVals = (taskID,)
    sql = "DELETE FROM task where id=?"
    logger.debug(f"SQL: {sql}")
    logger.debug(f"theVals: {theVals}")

    try:
        cursor = dbConn.cursor()
        cursor.execute(sql, theVals)
        dbConn.commit()
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    logger.info(f"taskid {taskID} deleted")
    return True


def getTaskID(dbConn, taskName):
    """Get the taskID from a task name

    Args:
      dbConn: database connection obj
      taskName: name of the task looking for. (case insensitve)

    Returns:
      list(taskID, taskName, taskDesc)(list length 0 nothing found)
    """
    logger.info(f"Getting taskid for task '{taskName}'")
    theVals = (taskName,)
    sql = "SELECT task.id as taskID, task.name as taskName, desc as taskDesc FROM task WHERE name = ?"
    logger.debug(f"SQL: {sql}")
    logger.debug(f"theVals: {theVals}")
    try:
        cursor = dbConn.cursor()
        cursor.execute(sql, theVals)
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    result = cursor.fetchone()
    logger.info(f"returning {result}")
    return result


def rptHours(dbConn, startDateUTC, endDateUTC, taskName=None):
    """Return a list of hours worked by mont for the taskName

    Args:
      dbConn: database connection obj
      startDateUTC: datetime obj in UTC time. This is the start time
      endDateUTC: datetime obj in UTC time. This is the end date(inclusive).
      taskName: name of the task looking for. (case insensitve)

    Returns:
      list(trackDateLocal, taskName, hours_Worked)
    """
    logger.info(
        f"startDateUTC: {startDateUTC.isoformat()}, endDateUTC: {endDateUTC.isoformat()}, taskName: {taskName}")

    logger.info(
        f"Getting hours worked from {startDateUTC.isoformat()} to {endDateUTC.isoformat()}")
    theVals = {'taskName': taskName,
               'startDateUTC': startDateUTC, 'endDateUTC': endDateUTC}
    logger.debug(f"theVals: {theVals}")
    selectSQL = """Select strftime("%Y-%m-%d", datetime(strftime("%s", started), 'unixepoch', 'localtime')) as trackDateLocal, task_name, sum(hours_worked) as hours_worked FROM v_hours_wrked_detail as vWrkDetail """
    groupBySQL = "GROUP BY strftime('%Y-%m-%d',datetime(strftime('%s',started),'unixepoch', 'localtime')), task_name "
    orderBySQL = "ORDER BY strftime('%Y-%m-%d',started) DESC "
    whereSQL = "WHERE started between date(:startDateUTC) and date(:endDateUTC,'+1 day')"
    if taskName:
        whereSQL += "AND task_name = :taskName "

    sql = selectSQL + whereSQL + groupBySQL + orderBySQL
    logger.debug(f"SQL: {sql}")
    cursor = dbConn.cursor()
    try:
        cursor.execute(sql, theVals)
    except Exception as err:
        logger.critical(f"Unexpected Error:  {err}", exc_info=True)
        sys.exit()

    rows = cursor.fetchall()
    logger.info(f"rows fetched: {len(rows)}")
    return rows


if __name__ == '__main__':
    pass
