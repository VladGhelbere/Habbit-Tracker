import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
from threading import Thread , Semaphore
from tornado.options import define, options
import json
import mysql.connector
import time
from datetime import datetime

authPassword = "authPassword"
define("port", default=9000, help="run on the given port", type=int)
block=Semaphore()
clients = []

# database management class
class DB:
    conn = None
    def __init__(self):
        self.connect()
    def connect(self):
        self.conn = mysql.connector.connect(
          host="host",
          user="user",
          passwd="passwd",
          database="database"
        )
        self.conn.autocommit = True
    def query(self, sql,params):
        cursor = self.conn.cursor()
        cursor.execute(sql,params)
        return cursor

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler)]
        tornado.web.Application.__init__(self, handlers, websocket_ping_interval=10)

class MainHandler(tornado.websocket.WebSocketHandler):
    deviceName = ""
    sensorId = 0
    SensorData = False
    timeStart = None
    timeStop = None
    duration = None

    def check_origin(self, origin):
        return True

    def open(self):
        if self.request.headers.get("Authpassword") != None and self.request.headers.get("Authpassword") == authPassword and self.request.headers.get("deviceName") != None:
            self.deviceName = self.request.headers.get("deviceName")
            global count,block
            block.acquire()
            clients.append(self)
            block.release()
            print(self.deviceName,"Connected with client id", len(clients))
            self.db=DB()
            # check if sensor in DB
            try:
                self.sensorId = (self.db.query((""" SELECT sensorId FROM habbit_tracker.sensors WHERE locName = %s ;"""), (self.deviceName,))).fetchone()[0]
                self.db.query(""" UPDATE habbit_tracker.sensors SET status = '1', ipAddress = %s WHERE sensorId = %s ;""", (self.request.remote_ip, self.sensorId,))
            # if not, insert it
            except:
                self.db.query(""" INSERT INTO habbit_tracker.sensors (locName, status, ipAddress) VALUES (%s, %s, %s) ;""", (self.deviceName, '1', self.request.remote_ip))
                self.sensorId = (self.db.query((""" SELECT sensorId FROM habbit_tracker.sensors WHERE locName = %s ;"""), (self.deviceName,))).fetchone()[0]
                print(self.sensorId)
        else:
            self.close()
            print("Connection refused")
    def on_close(self):
        # Update sensor status before disconnected
        self.db.query(""" UPDATE habbit_tracker.sensors SET status = '0' WHERE sensorId = %s ;""", (self.sensorId,))
        # If connection ended abruptly, end action timer, insert into DB
        if self.timeStart != None:
            self.timeStop = datetime.now()
            self.duration = (self.timeStop - self.timeStart).seconds/60
            print(self.duration)
            print("Stopped at",self.timeStop,"Duration", format(self.duration, '.2f'), "minutes")
            self.db.query(""" INSERT INTO habbit_tracker.events (sensorId, triggerStart, triggerEnd, duration) VALUES (%s, %s, %s, %s) ;""", (self.sensorId, self.timeStart.isoformat(timespec='seconds'), self.timeStop.isoformat(timespec='seconds'), self.duration))
        print(self.deviceName,"Disconnected with client id", clients.index(self))
        global count,block
        block.acquire()
        clients.remove(self)
        block.release()

    def on_message(self, message):
        jsonMessage = json.loads(message)
        print(jsonMessage, "Message recived from: ", self.deviceName)
        if "SensorData" in jsonMessage:
            self.SensorData = jsonMessage["SensorData"]
            if self.SensorData:
                self.timeStart = datetime.now()
                print("Started at",self.timeStart)
            else:
                self.timeStop = datetime.now()
                if self.timeStart != None:
                    self.duration = (self.timeStop - self.timeStart).seconds/60
                    if (self.duration > 0.05) or ("door" in self.deviceName and self.duration < 0.05):
                        print("Stopped at",self.timeStop,"Duration", format(self.duration, '.2f'), "minutes")
                        self.db.query(""" INSERT INTO habbit_tracker.events (sensorId, triggerStart, triggerEnd, duration) VALUES (%s, %s, %s, %s) ;""", (self.sensorId, self.timeStart.isoformat(timespec='seconds'), self.timeStop.isoformat(timespec='seconds'), self.duration))
                self.timeStart = None
                self.timeStop = None

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
