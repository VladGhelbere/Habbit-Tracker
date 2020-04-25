from dateutil.relativedelta import *
import datetime
import pymysql
import json

def connectToMySQL(host, port, user, password, db):
    db = pymysql.connect(host=host,   
                     port=port,
                     user=user,        
                     passwd=password, 
                     db=db)
    return db

def getLastPeriodEntries(startTime, endTime):
    query = "  SELECT t1.locName, SUM(t2.duration) FROM sensors t1, events t2 WHERE (t1.idx = t2.sensorId) AND (t2.triggerEnd >= %s AND t2.triggerEnd <= %s) GROUP BY locName "
    params = (startTime, endTime)
    cursor.execute(query,params)
    db_data = cursor.fetchall()

    data_dict = {}

    for entry in db_data:
        data_dict[entry[0]] = int(entry[1])

    return data_dict

def getSensorId(key):
    query = "  SELECT idx FROM sensors WHERE locName = %s   "
    params = (key)
    cursor.execute(query,params)
    db_data = cursor.fetchone()
    return db_data[0]

def registerToDb(diff_dict):

    sensorId = getSensorId(diff_dict['key'])
    query = "   INSERT INTO differences (sensorId, from_date, to_date, difference, percentage) VALUES (%s, %s, %s, %s, %s)  "
    params = (sensorId, time_one_month_ago, time_today, diff_dict['difference'], diff_dict['percentage'])
    print(params)
    cursor.execute(query,params)
    print("Done")

    db.commit()



time_today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
time_one_month_ago = (datetime.datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S") 
time_two_months_ago = (datetime.datetime.now() - relativedelta(months=2)).strftime("%Y-%m-%d %H:%M:%S") 


print(time_today)
print(time_one_month_ago)
print(time_two_months_ago)

db = connectToMySQL("db_ipadress","db_port","db_username","db_pass","db_name")    
cursor = db.cursor()

last_two_months_data_dict = getLastPeriodEntries(time_two_months_ago, time_one_month_ago)
last_month_data_dict = getLastPeriodEntries(time_one_month_ago, time_today)

print(last_two_months_data_dict.keys())
print(last_two_months_data_dict.values())

print(last_month_data_dict.keys())
print(last_month_data_dict.values())

# print(differences_dict)
# registerToDb(differences_dict)

data_dict = {}

for key, value in last_two_months_data_dict.items():
    for key2, value2 in last_month_data_dict.items():
        if (key == key2):
            difference = value2-value
            
            if (value > value2):
                percentage = round((- ((value2 * 100) / value)),1)
            else:
                percentage = round((100 - ((value * 100) / value2)),1)

            data_dict['key'] = key
            data_dict['difference'] = difference
            data_dict['percentage'] = percentage
    
    registerToDb(data_dict)



db.close()