import http.client, urllib
import requests
import json
import pandas as pd
import time
import requests

# Disable the ssl warnings of Unifi
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Import the settings
import configparser
import os
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_file)

# Bind variables
polltime_away = int(config['Logic']['polltime_away'])
polltime_found = int(config['Logic']['polltime_found'])
unifi_user = config['Unifi']['unifi_user']
unifi_password = config['Unifi']['unifi_password']
unifi_devicename = config['Unifi']['unifi_devicename']
unifi_url = config['Unifi']['unifi_url']
dsm_user = config['DSM']['dsm_user']
dsm_password = config['DSM']['dsm_password']
dsm_url = config['DSM']['dsm_url']
pushover_user = config['Pushover']['pushover_user']
pushover_token = config['Pushover']['pushover_token']
pushover_prefix = config['Pushover']['pushover_prefix']

# -- FUNCTIONS -- 
# The Pushover message creator
def message(message):
	conn = http.client.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",urllib.parse.urlencode({
	"token": pushover_token,
	"user": pushover_user,
	"message": pushover_prefix + message,}), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()
	print('Message: ' + message + ' sent')
	return

# -- FUNCTION -- DSM Login
def dsm_login(user,password):
    conn = http.client.HTTPConnection(dsm_url)
    conn.request("GET", "/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account=" + user + "&passwd=" + password + "&session=SurveillanceStation&format=sid")
    res = conn.getresponse()
    data = res.read()
    result = json.loads(data.decode("utf-8"))
    result = str(result['data']['sid'])
    return result

# -- FUNCTION -- DSM Logout
def dsm_logout(sid):
    conn = http.client.HTTPConnection(dsm_url)
    conn.request("GET", "/webapi/auth.cgi?api=SYNO.API.Auth&method=Logout&version=2&session=SurveillanceStation&_sid=" + sid)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")

# -- FUNCTION -- Disable the camera
def dsm_disable_camera(sid):
	conn = http.client.HTTPConnection(dsm_url)
	conn.request("GET", "/webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=Disable&version=9&idList=1&_sid=" + sid)
	res = conn.getresponse()
	data = res.read()
	message('Camera disabled: ' + data.decode("utf-8"))
	return data.decode("utf-8")

# -- FUNCTION -- Enable the camera
def dsm_enable_camera(sid):
	conn = http.client.HTTPConnection(dsm_url)
	conn.request("GET", "/webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=Enable&version=9&idList=1&_sid=" + sid)
	res = conn.getresponse()
	data = res.read()
	message('Camera enabled: ' + data.decode("utf-8"))
	return data.decode("utf-8")

# -- FUNCTION -- The Unifi Controller login
def login_unifi():
    url = unifi_url + '/login'
    payload = {"username":unifi_user,"password":unifi_password, "remember": "true", "strict": "true"}
    r = requests.post(url, data=json.dumps(payload),verify=False)
    return r.cookies

# -- FUNCTION -- The Unifi Controller logout (not used, but for testing)
def logout_unifi(resultcookies):
    url = unifi_url + '/logout'
    r = requests.post(url, cookies=resultcookies, verify=False)
    return

# -- FUNCTION -- The Unifi Controller poller
def check_unifi(name,resultcookies):
    url = unifi_url + '/s/default/stat/sta'
    req = requests.get(url, cookies=resultcookies,verify=False)
    # If the return status code is 401 mostlikly the login is not valid anymore
    if (req.status_code == 401):
        message('Not logged in, statuscode: ' + str(req.status_code))
        message('Re-Login in progress')
        time.sleep(30)
        resultcookies = login_unifi()
        time.sleep(30)
        url = unifi_url + '/s/default/stat/sta'
        req = requests.get(url, cookies=resultcookies,verify=False)
        message('Current statuscode: ' + str(req.status_code))
        # Sending raw data to messenger to see if it's working again (dirty)
        message(req.text)
    requeststext = req.text
    result = json.loads(requeststext)
    result = str(result['data'])
    result = result.replace("'",'"')
    result = result.replace("False",'"False"')
    result = result.replace("True",'"True"')
    df = pd.read_json(result)
    result = df[(df.name == name)]
    row_num = result.shape[0]
    row_num = str(row_num)
    return_result = {'row_num': row_num, 'resultcookies': resultcookies}
    return return_result
# End of functions

# -- LOGIC -- Application logic
# Initial Unifi Login
resultcookies = login_unifi()
# Initial startup camera
sid = dsm_login(dsm_user,dsm_password)
dsm_enable_camera(sid)
dsm_logout(sid)

# Loop for checking
while True:
	found = check_unifi(unifi_devicename,resultcookies)
	resultcookies = found['resultcookies']
	if (found['row_num'] == '1'):
		sid = dsm_login(dsm_user,dsm_password)
		dsm_disable_camera(sid)
		dsm_logout(sid)
		message('Phone: ' + unifi_devicename + ', found')
		while (found['row_num'] == '1'):
			time.sleep(polltime_found)
			found = check_unifi(unifi_devicename,resultcookies)
			resultcookies = found['resultcookies']
			print('Phone: ' + unifi_devicename + ' still inside')
		sid = dsm_login(dsm_user,dsm_password)
		dsm_enable_camera(sid)
		dsm_logout(sid)
		message('Phone ' + unifi_devicename + ' has left the building')
	else:
		print('Nothing to do, result: ' + found['row_num'])
	time.sleep(polltime_away)