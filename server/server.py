from flask import Flask,request
from flask_cors import CORS, cross_origin
import json
import os
import hashlib
from random import randint

import smtplib
from flask_mysqldb import MySQL

# 2-factor authentication part
fromEmail = "daltourism@gmail.com"
password = "ebsxnukedqyqzmrx"
def sendOTP(emailId, otp):
    with smtplib.SMTP('smtp.gmail.com',587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(fromEmail,password)
        subject = "DalTourism Signup OTP"
        body = "Your OTP is "+str(otp)
        msg = f'Subject:{subject}\n\n{body}'
        smtp.sendmail(fromEmail,emailId,msg)
# 2-factor authentication ends here

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MYSQL_HOST'] = 'database-1.cmr8tyiaftvb.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'cloudproject'
app.config['MYSQL_DB'] = 'daltourism'

mysql= MySQL(app)

# request success
requestSuccess = {}
requestSuccess['status'] = 200
requestSuccess['message'] = 'success'

# request success
requestFailed = {}
requestFailed['status'] = 401
requestFailed['message'] = 'failed'

loginFailure = {}

# login endpoint
@app.route('/login', methods = ['POST'])
@cross_origin()
def login():
    loginData = decodeData(request.json)
    emailId=loginData['email']
    password=hashString(loginData['password'])
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT userId,emailId,password FROM users WHERE emailId= %s AND password = %s', (emailId, password))
    account=cursor.fetchone()
    if(account is not None):
        if(emailId==account[1] and password==account[2]):
            cur = mysql.connection.cursor()
            requestSuccess["userId"] = account[0]
            otp=randint(10000,70000)
            cur.execute("INSERT INTO otp(userId, emailId, otp) VALUES (%s, %s, %s)",(account[0],emailId,otp))
            mysql.connection.commit()
            sendOTP(emailId, otp)
            return requestSuccess
        else:
            return requestFailed
    else:
         return requestFailed

# signup endpoint
@app.route('/signup', methods = ['POST'])
@cross_origin()
def signup():
    signUpData = decodeData(request.json)
    firstName = signUpData['firstName']
    lastName  = signUpData['lastName']
    emailId = signUpData['emailId']
    password = hashString(signUpData['password'])
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(firstName, lastName, emailId, password) VALUES (%s, %s, %s, %s)",(firstName,lastName,emailId,password))
    otp=randint(10000,70000)
    sendOTP(emailId, otp)
    userId= cur.lastrowid
    requestSuccess["userId"] = userId
    cur.execute("INSERT INTO otp(userId, emailId, otp) VALUES (%s, %s, %s)",(userId,emailId,otp))
    mysql.connection.commit()
    cur.close()
    return requestSuccess

# validate OTP
@app.route('/validateOTP', methods = ['POST'])
@cross_origin()
def validateOTP():
    userId = request.args.get('userId')
    optData = decodeData(request.json)
    cur = mysql.connection.cursor()
    query = "select userId,otp from otp where userId="+str(userId)+" order by rowId desc limit 1";
    cur.execute(query)
    queryResult = cur.fetchall()
    if any(map(len, queryResult)) and optData['otp']==queryResult[0][1]:
        return requestSuccess
    else:
        return requestFailed

# search for locations endpoint
@app.route('/locations', methods = ['GET'])
@cross_origin()
def locations():
    searchKeyWord = request.args.get('search')
    list_1=[]
    dict_items={}
    dict_items['locations']={}
    query = ""
    if searchKeyWord is not None:
        query = 'select * from locations where province like "%'+searchKeyWord+'%" or name like "%'+searchKeyWord+'%";'
    else:
        query = "SELECT * from locations"
    cur = mysql.connection.cursor()
    cur.execute(query)
    locations= cur.fetchall()    
    for i in range(len(locations)):
       dict_items={
            'id': locations[i][0],
            'name':locations[i][1],
            'description':locations[i][2],
            'province':locations[i][3],
            'distance':locations[i][4],
            'price':locations[i][5],
            'url':locations[i][6]
             }
       list_1.append(dict_items)
    data = {}
    data["data"] = {"locations":encodeArray(list_1)}
    data["status"] = 200
    return data


# validate OTP
@app.route('/bookTickets', methods = ['POST'])
@cross_origin()
def bookTickets():
    cardNumber = request.args.get('cardNumber')
    val=[]
    tickets = decodeData(request.json)
    for i in tickets.values():
        val.append(i)
    userId = val[0]
    locationId = val[1]
    tickets= val[2]
    date= val[3]
    overallCost=val[4]
    if cardNumber != "1111111111111111":
        return requestFailed
    else:
        cur = mysql.connection.cursor()
        ticketCode = str(randint(50000,70000))
        cur.execute("INSERT INTO tickets(userId, locationId, tickets, date, overallCost, ticketCode) VALUES (%s, %s, %s, %s, %s, %s)",(userId,locationId,tickets,date,overallCost,ticketCode))
        mysql.connection.commit()
        return requestSuccess

# validate OTP
@app.route('/getTickets', methods = ['GET'])
@cross_origin()
def getTickets():
    userId = request.args.get('userId')
    list_tickets=[]
    cur = mysql.connection.cursor()
    query = "select locations.name, locations.decription, locations.province, locations.distance, locations.price, tickets.overallCost,tickets.tickets,tickets.userId,tickets.date, tickets.ticketCode from locations join tickets on locations.id = tickets.locationId where tickets.userId="+userId+" order by tickets.ticketId desc limit 1"
    cur.execute(query)
    gettickets= cur.fetchall()
    for i in range(len(gettickets)):
        dict_items1={
            'userId': gettickets[i][7],
            'locationName':gettickets[i][0],
            'description': gettickets[i][1],
            'province': gettickets[i][2],
            'distance': gettickets[i][3],
            'date':gettickets[i][8],
            'price': gettickets[i][4],  
            'overallPrice':gettickets[i][5],
            'tickets':gettickets[i][6],
            'ticketCode': gettickets[i][9]
        } 
        list_tickets.append(dict_items1)
    data = {}
    if any(map(len, gettickets)):
        data["data"] = {"ticket":encodeObj(list_tickets[0])}
        data["status"] = 200
        return data
    else:
        return requestFailed

# validate OTP
@app.route('/emailTicket', methods = ['GET'])
@cross_origin()
def emailTicket():
    userId = request.args.get('userId')
    query = "select l.name, l.province, t.overallCost, t.tickets, t.date, t.ticketCode from locations as l join tickets as t on l.id = t.locationId where t.userId = "+userId+" order by t.ticketId desc limit 1;"
    cur = mysql.connection.cursor()
    cur.execute(query)
    gettickets= cur.fetchall()
    emailBody = "Your ticket: \n\n"
    for i in range(len(gettickets)):
        emailBody += "Place: "+gettickets[i][0]
        emailBody += "\nProvince: "+gettickets[i][1]
        emailBody += "\nOverall Cost: "+gettickets[i][2]
        emailBody += "\nTickets: "+gettickets[i][3]
        emailBody += "\nDate: "+gettickets[i][4]
        emailBody += "\nTicket Code: "+gettickets[i][5]
    emailQuery = "select emailId from users where userId="+userId
    cur.execute(emailQuery)
    emailId = cur.fetchall()
    emailId = emailId[0][0]
    with smtplib.SMTP('smtp.gmail.com',587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(fromEmail,password)
        subject = "Ticket Confirmation"
        body = emailBody
        msg = f'Subject:{subject}\n\n{body}'
        smtp.sendmail(fromEmail,emailId,msg)
    print(emailId)
    return requestSuccess

def encodeString(string):
    outputString = ""
    temp = string[0]
    count = 1
    for i in range(1,len(string)):
        currentChar = string[i]
        if currentChar == temp:
            count += 1
        else:
            outputString += temp + str(count)
            count = 1
        temp = currentChar
    outputString += temp + str(count)
    return outputString

def encodeObj(data):
    for key in data:
        data[key] = encodeString(str(data[key]))
    return data

def encodeArray(data):
    for i in range(0,len(data)):
        data[i] = encodeObj(data[i])
    return data

def decodeString(string):
    tempString = ""
    i = 0
    while i < len(string):
        count = int(string[i+1])
        for j in range(0,count):
            tempString += string[i]
        i += 2
    return tempString

def decodeData(data):
    for key in data:
        data[key] = decodeString(data[key])
    return data

def hashString(string):
    # SHA256 encryption used for generating the hash
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


# url to be given in the util services
