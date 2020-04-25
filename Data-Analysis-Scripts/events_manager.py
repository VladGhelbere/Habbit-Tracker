from dateutil.relativedelta import *
import datetime
import pymysql
import json

class Entry:
    def __init__ (self, idx, sensorName, startTime, endTime, duration, activity):
        self.idx = idx
        self.sensorName = sensorName
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration
        self.activity = activity

    def categorizeActivity(self):
        if (self.sensorName == "Bed"):
            if (self.duration/60 > 4.5):
                self.activity = 'Sleeping'
            if (self.duration/60 >= 2):
                self.activity = 'Napping/Relaxing'
            if (self.duration/60 < 2):
                self.activity = 'Relaxing'

        if (self.sensorName == "Desk"):
            self.activity = 'On the computer'

        if (self.sensorName == "Kitchen"):
            if (self.duration/60 >= 1):
                self.activity = 'Cooking/Eating'
            if (self.duration/60 < 1):
                self.activity = 'Eating'

    def registerActivity(self):
        query = "   INSERT INTO activities (idx, locName, triggerStart, triggerEnd, duration, activity) VALUES (%s, %s, %s, %s, %s, %s)  "
        params = (self.idx, self.sensorName, self.startTime, self.endTime, self.duration, self.activity)
        cursor.execute(query,params)
        db.commit()

def connectToMySQL(host, port, user, password, db):
    db = pymysql.connect(host=host, port=port, user=user, passwd=password, db=db)
    return db

def getLastPeriodEntries(fromTime):
    query = """   SELECT events.idx, sensors.locName, events.triggerStart, events.triggerEnd, events.duration FROM events, sensors WHERE events.sensorId = sensors.sensorId AND events.triggerStart > %s   """
    params = (fromTime)
    cursor.execute(query,params)
    db_data = cursor.fetchall()
    return db_data



time_today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
time_yesterday = (datetime.datetime.now() - relativedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S") 

db = connectToMySQL("db_ipadress","db_port","db_username","db_pass","db_name")   
cursor = db.cursor()

db_entries = getLastPeriodEntries(time_yesterday)
currentEntry = Entry(0,"",None,None,0,"")

for entry in db_entries:
    idx = entry[0]
    sensorName = entry[1]
    startTime = entry[2]
    endTime = entry[3]
    duration = entry[4]
    if (currentEntry.sensorName != sensorName):
        if (currentEntry.sensorName != ""):
            currentEntry.categorizeActivity()
            print(currentEntry.idx, currentEntry.sensorName, currentEntry.startTime, currentEntry.endTime, currentEntry.duration, currentEntry.activity)
            currentEntry.registerActivity()
        currentEntry = Entry(idx,sensorName,startTime,endTime,duration,"")
    else:
        currentEntry.idx = idx
        currentEntry.endTime = endTime
        currentEntry.duration += duration

currentEntry.categorizeActivity()
print(currentEntry.idx, currentEntry.sensorName, currentEntry.startTime, currentEntry.endTime, currentEntry.duration, currentEntry.activity)
currentEntry.registerActivity()
