# python script for interactively fetching license information given a callsign
# Uses HamQTH API, see https://www.hamqth.com/developers.php
# You must have a HamQTH account as the API requires a valid username and password to start a session

import configparser
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta

import requests

# BEGIN FUNCTION DEFINITIONS

# This function requests a new session from the HamQTH API
def getsession():
    sessionReq = requests.get('https://www.hamqth.com/xml.php?u={}&p={}'.format(username, password))
    sessionReq.raise_for_status()               # check whether HTTP request was successful
    ## need to handle exception for timeouts/network errors etc here, add retry loop
    root = ET.fromstring(sessionReq.content)    # get XML tree from HTTPS request results
    sessionID = root[0][0].text
    if sessionID == 'Wrong user name or password':
        print("Wrong user name or password! Please enter valid HamQTH.com credentials in cf.conf")
        sys.exit(1)         # exit if credentials are wrong. eventually will implement input prompts for new credentials
    else:
        expireTime = datetime.now() + timedelta(hours = 1)
        config.set('Session', 'SID', str(sessionID))
        config.set('Session', 'EXP', str(expireTime))
        config.write(open('cf.conf','w'))
        print('Connected to HamQTH.com as {}\nSession ID: {}\nExpires {}'.format(username, sessionID, expireTime.strftime('%H:%M:%S')))  # session is valid for one hour, print expiration time when new session is requested
        return sessionID

# This function validates input of callsign to be looked up, additional validation will be added here later
def inputcallsign():
    callsign = ''
    while True:
        callsign = input('Enter Callsign to Lookup:')
        if len(callsign) < 3 or len(callsign) > 7:
            print('{} does not appear to be a valid callsign format, please try again.'.format(callsign))
            callsign = ''
            continue
        else:
            return callsign

# This function requests information from the HamQTH API given a valid session ID and callsign, returns info in a dict
def fetchcallsigndata(session_id, callsign):
    callsignreq = requests.get('https://www.hamqth.com/xml.php?id={}&callsign={}&prg=callsignfetch'.format(session_id, callsign))
    callsignreq.raise_for_status()      #check whether HTTP request was successful
    csroot = ET.fromstring(callsignreq.content)
    qtherror = csroot.find('*/{https://www.hamqth.com}error')
    if qtherror:
        print('HamQTH Error: {}'.format(qtherror.text))
        return False
    else:
        csdict = {}
        for child in csroot[0]:
            tag = child.tag
            csdict[tag.split('}')[1]] = child.text
    return csdict

def print_callsign_info(print_these_fields, callsign_dictionary):
    if not print_these_fields:  # if no parameter is passed, populate this list with default values
        print_these_fields = ['nick', 'qth', 'grid', 'email'] # these are the fields that will be printed by default
    # field_labels dict contains the human-friendly labels for each field the API may return
    field_labels = {'nick': 'Nickname',
                    'adr_name' : 'Name (from address)',
                    'qth' : 'QTH',
                    'country' : 'Country',
                    'grid' : 'Grid Square',
                    'email' : 'Email address'}
    for key in print_these_fields & field_labels.keys() & callsign_dictionary.keys():
        print('{}: {}'.format(field_labels[key], callsign_dictionary[key]))
# END FUNCTION DEFINITIONS

# MAIN SEQUENCE BEGIN
config = configparser.ConfigParser()
config.read('cf.conf')                              # read configuration file cf.conf
username = config.get('Credentials', 'User')        # The user's callsign is read from cf.conf
password = config.get('Credentials', 'Password')    # HamQTH password is read from cf.conf
expireTime = config.get('Session', 'EXP')           # Existing session expiration date/time read from cf.conf

# If there is no saved session, or saved session is expired, run getsession
if expireTime == '' or datetime.now() >= datetime.strptime(expireTime.split('.')[0], '%Y-%m-%d %H:%M:%S'):
    sid = getsession()
else:
    sid = config.get('Session', 'SID')              # Read existing session ID from cf.conf
    print('Existing session found\nSession ID: {}'.format(sid))

# MAIN LOOP BEGIN
while True:
    callsign = inputcallsign()  # call function for user input and input validation
    callsign_results = fetchcallsigndata(sid, callsign) # using session ID and callsign, request info from API and return as dict
    print_callsign_info([], callsign_results)   # Print results from API request in human-friendly formatting
    # Ask if we want to lookup another callsign
    again = input("Do you want to lookup another callsign? (y/n) ").lower()
    if again == 'y':
        continue
    elif again == 'n':
        break


