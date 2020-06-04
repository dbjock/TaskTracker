from datetime import datetime, timezone

class DailyTaskWrkedHours(object):
    def __init__(self,taskName,dateUTC,hoursDec):
        """
        taskName = string. Name of the task
        dateUTC = dateOBJ UTC timezone
        hoursDec = hours worked in decimal.
        """
        self.taskName = taskName
        self.dateUTC = dateUTC
        self.hoursDec = hoursDec

    def localUTC(self):
        """dateUTC convereted to local TZ aware"""
        return self._utc2Local()

    def _utc2Local(self):
        """ return local timezone TZ aware object form utc_dt"""
        utc_dt = datetime.strptime(self.dateUTC,'%Y-%m-%d')
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def hoursDT(self):
        """hoursDec converted to HH:MM or string error over 24HR"""
        xHours = int(self.hoursDec)
        xMinutes = int((self.hoursDec - xHours)*60)
        if xHours >= 24:
            return "ERROR Over 24 hours"
        else:
            wrkd_M = self.localUTC().month
            wrkd_D = self.localUTC().day
            wrkd_Y = self.localUTC().year
            workedDT = datetime(wrkd_Y, wrkd_M, wrkd_D, xHours, xMinutes)
            return workedDT.strftime('%H:%M')
