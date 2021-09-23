#Import Reqeusts to get the webpage from DNA Center
import requests
# Import HTTPBasicAuth to authenticate to DNA Center
from requests.auth import HTTPBasicAuth
# Bypass certificate warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# Import json to return the results from the get request in a json format
import json
import difflib
# This is used to write the results to a csv file.
import csv
# This allows the csv filename to include the timestamp
import datetime as dt
# This is not really needed, but it was imported to insert pauses during the script creation for troubleshooting purposes.
import time
# time.sleep(10) pauses for 10 seconds
# This enables encoding the username and password to receive a token from DNA Center
import base64
# Get path
import os
#This imports my credentials from the creds.py file
import creds
# currentIndex is used for paging if necessary
currentIndex = 0
# Today's date
currentDate = dt.datetime.today().strftime('%m-%d-%Y-%Hh-%Mm-%Ss')
# This is used to control the paging while loop
countResults = 0
# Suppress Insecure Requests Warnings for self-signed certificate on DNA Center
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Specify the DNA Center Server
#dnacServer = "172.21.21.10"
# Prompt the user for the DNA Center Server
dnacServer = input('Enter DNA Center Server IP Address:\n')

# Username and password used to create the token
myUserName = creds.myUserName
myPassword = creds.myPassword
#myUserName = input('Username:\n')
#myPassword = input('Password:\n')
myUserPass = myUserName + ":" + myPassword
#print(myUserPass)

# Encode the username and password to submit as a header when creating the token
encodedUserPass = str(base64.b64encode(bytes(myUserPass, "utf-8")))
encodedLength = len(encodedUserPass) - 1
encodedUserPass = encodedUserPass[2:encodedLength]
encodedUserPass = "Basic "+encodedUserPass

# Specify the URL to create a token
tokenURL = "https://"+dnacServer+"/dna/system/api/v1/auth/token"
# Create the header used to create the token
headersToken = {
    'Authorization': encodedUserPass
    }
# Create the token
myTokenResponse = requests.post(tokenURL, headers=headersToken, verify=False)
myTokenDict = myTokenResponse.json()
# Creating a token returns a Dictionary where the attribute is Token and the value is the actual token
myToken = myTokenDict['Token']
print("********************************************DNA Center Device Archive********************************************")
# Get list of Device IDs 
url = "https://"+dnacServer+"/dna/intent/api/v1/network-device"
payload = {}
headers = {
  'X-Auth-Token': myToken,
  'Authorization': encodedUserPass
}

myDeviceList = []
#deviceIdList = requests.get(url, headers=headers, data = payload, verify=False)
response = requests.get(url, headers=headers, data =payload, verify=False)
response_json = response.json()
responseList = response_json["response"]
for i in responseList:
    addDevice = False
    for x,y in i.items():
        if x == "family":
            if y == "Wireless Controller" or y == "Switches and Hubs" or y == "Routers":
                addDevice = True
        if x == "id" and addDevice == True:
            currentDevice = y
            myDeviceList.append(currentDevice)

# Convert myDeviceList to string
formattedDeviceList = ', '.join('"{0}"'.format(i) for i in myDeviceList)


# This creates the tasks required to archive the configs
taskURL = "https://"+dnacServer+"/dna/intent/api/v1/network-device-archive/cleartext"
payload="{\"deviceId\": ["+formattedDeviceList+"],\"password\": \"Cisco123\"}"
#payload={"deviceId":"+myDeviceList+",""password":"Password1!"}

postHeaders = {
  'X-Auth-Token': myToken,
  'Authorization': encodedUserPass,
  'Content-Type': 'application/json',
}

taskResponse = requests.request("POST", taskURL, headers=postHeaders, data=payload, verify=False)
taskResponse_json = taskResponse.json()
taskResponseDict = taskResponse_json["response"]
for x,y in taskResponseDict.items():
    if x == 'url':
        myTaskURL = y

# Get the file information from the taskId
fileURL = "https://"+dnacServer+"/dna/intent"+myTaskURL
payload={}
# This will continue to run the request until the task run earlier completes
attempts = 0
while True:
    time.sleep(5)
    attempts = attempts + 1
    fileResponse = requests.get(fileURL, headers=headers, data = payload, verify=False)
    fileResponse_json = fileResponse.json()
    fileResponseDict = fileResponse_json["response"]
    if fileResponseDict['progress'] == "Device configuration Successfully exported as password protected ZIP.":
        myStatusURL = fileResponseDict['additionalStatusURL']
        break
    if attempts > 60:
        print("Something went wrong.  Please troubleshoot the API call or increase the wait time and/or number of attempts.")
        break

# Get Zipped File
url = "https://"+dnacServer+"/dna/intent"+myStatusURL
fileNamePieces = myStatusURL.split('/')
fileName = fileNamePieces[4]
response = requests.get(url, headers=headers, verify=False, allow_redirects=True)
open(fileName, 'wb').write(response.content) 
filePath = os.getcwd()
print("Operation Complete!")
print("Zipped file was saved to: " +filePath+"/"+fileName)
time.sleep(300)







