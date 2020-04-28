from flask import Flask     # library needed for Flask sv
from flask import jsonify   # library needed for Flask sv
from flask import request   # library needed for Flask sv
from dateutil.relativedelta import *    # library needed for Flask sv
import datetime     # library needed for dates formatting
import calendar     # library needed for dates formatting
import pymysql      # pymysql used for mysql connection
import json         # needed to JSONIFY some data

# initialize flask sv
app = Flask(__name__)

# function to connect to DB
def connectToMySQL(host, port, user, password, db):
    db = pymysql.connect(host=host, port=port, user=user, passwd=password, db=db)
    return db

# function to fetch data from DB
def getLastPeriodEntries(startTime, endTime, cursor):
    
    # build variable to hold the number of days in the startTime month variable (to be used for averaging)
    temp_date = startTime.replace(day=calendar.monthrange(startTime.year, startTime.month)[1]).day
    
    # format the period of time into strings to use in query
    startTime = startTime.strftime("%Y-%m-%d %H:%M:%S") 
    endTime = endTime.strftime("%Y-%m-%d %H:%M:%S") 

    # build and execute query
    query = "  SELECT t1.locName, SUM(t2.duration) FROM sensors t1, events t2 WHERE (t1.sensorId = t2.sensorId) AND (t2.triggerEnd >= %s AND t2.triggerEnd <= %s) GROUP BY locName "
    params = (startTime, endTime)
    cursor.execute(query,params)
    
    # fetch data from DB
    db_data = cursor.fetchall()
    # initialize dictionary for DB data pairs
    data_dict = {}

    # build the DB data pairs
    for entry in db_data:
        # calculate average per location per day
        data_dict[entry[0]] = int(entry[1])/temp_date

    # return the dictionary
    return data_dict


# function to check flask back-end
@app.route('/')
def backendAvilable():
    return {"response":"200 - All Good !"}

# function to search for certain data JSONS
@app.route('/search', methods=['POST'])
def search():
    return jsonify(['Data'])

# function to calculate the data and send it to grafana
@app.route('/query', methods=['POST'])
def query():

    # get first day of last month and last day of last month period
    time_one_month_ago_start = (datetime.datetime.now() - relativedelta(months=1)).replace(day=1)
    time_one_month_ago_end = time_one_month_ago_start.replace(day=calendar.monthrange(time_one_month_ago_start.year, time_one_month_ago_start.month)[1])

    # get first day of current month and last day of current month period
    first_day_of_month = datetime.datetime.now().replace(day=1)
    last_day_of_month = first_day_of_month.replace(day=calendar.monthrange(first_day_of_month.year, first_day_of_month.month)[1])

    # connect to DB and initialize cursor
    db = connectToMySQL("ipadress","port","user","password","db_name")   
    cursor = db.cursor()

    # fetch the data from DB into these dictionaries
    last_month_data_dict = getLastPeriodEntries(time_one_month_ago_start, time_one_month_ago_end, cursor)
    current_month_data_dict = getLastPeriodEntries(first_day_of_month, last_day_of_month, cursor)

    # initialize variables used for building the response JSON
    target = []
    datapoints = []

    # get some data from Grafana
    grafana_req=request.get_json()
    panelId = (grafana_req['panelId'])

    # match keys from the two data sets
    for key, value in last_month_data_dict.items():
        for key2, value2 in current_month_data_dict.items():
            if (key == key2):
                # if request needs raw data values, build JSON one way
                if (panelId == 8):
                    data = value2-value
                    temp = list((data,key))
                    datapoints.append(temp)
                # if request needs percentages, build JSON another way
                if (panelId == 9):
                    if (value > value2):
                        data = round((- ((value2 * 100) / value)),1)
                    else:
                        data = round((100 - ((value * 100) / value2)),1)
                    temp = list((data,key))
                    datapoints.append(temp)

                # define final JSON structure
                target.append({'target':'Data', 'datapoints':datapoints.copy()})
                # clear temporary variable for next request
                datapoints.clear()

    # return the response JSON
    return jsonify(target)

    # close the connection to the DB so it doesn't remain open while dashboard stays open
    db.close()
    

# run the Flask sv.
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)
