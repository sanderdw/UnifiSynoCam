import http.client, urllib
import requests
import json
import pandas as pd
import time
import requests

# Disable the ssl warnings of Unifi Controller
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Import the settings
import configparser
import os
config = configparser.ConfigParser()
config_file = 'config.ini'
#config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_file)

# Bind variables
polltime_away = int(config['Logic']['polltime_away'])
polltime_found = int(config['Logic']['polltime_found'])
unifi_user = config['Unifi']['unifi_user']
unifi_password = config['Unifi']['unifi_password']
unifi_devicenames = config['Unifi']['unifi_devicenames'].split(",")
unifi_devicenames_text = config['Unifi']['unifi_devicenames']
unifi_url = config['Unifi']['unifi_url']
unifi_site = config['Unifi']['unifi_site']
dsm_user = config['DSM']['dsm_user']
dsm_password = config['DSM']['dsm_password']
dsm_url = config['DSM']['dsm_url']
dsm_camera_ids = config['DSM']['dsm_camera_ids']
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
def dsm_login():
    conn = http.client.HTTPConnection(dsm_url)
    conn.request("GET", "/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account=" + dsm_user + "&passwd=" + dsm_password + "&session=SurveillanceStation&format=sid")
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
	conn.request("GET", "/webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=Disable&version=9&idList="+ dsm_camera_ids +"&_sid=" + sid)
	res = conn.getresponse()
	data = res.read()
	message('Camera disabled: ' + data.decode("utf-8"))
	return data.decode("utf-8")

# -- FUNCTION -- Enable the camera
def dsm_enable_camera(sid):
	conn = http.client.HTTPConnection(dsm_url)
	conn.request("GET", "/webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=Enable&version=9&idList="+ dsm_camera_ids +"&_sid=" + sid)
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
def check_unifi(resultcookies):
	url = unifi_url + '/s/' + unifi_site + '/stat/sta'
	req = requests.get(url, cookies=resultcookies,verify=False)
    # If the return status code is 401 mostlikly the login is not valid anymore
	if (req.status_code == 401):
		message('Not logged in, statuscode: ' + str(req.status_code))
		message('Re-Login in progress')
		resultcookies = login_unifi()
		time.sleep(30)
		url = unifi_url + '/s/' + unifi_site + '/stat/sta'
		req = requests.get(url, cookies=resultcookies,verify=False)
		message('Current statuscode: ' + str(req.status_code))
		# Sending raw data to messenger to see if it's working again (dirty)
		message(req.text)
	requeststext = req.text
	result = json.loads(requeststext)
	result = str(result['data'])
	# Fix json notation
	result = result.replace("'",'"')
	result = result.replace("False",'"False"')
	result = result.replace("True",'"True"')
	df = pd.read_json(result)
	result = df[df['name'].isin(unifi_devicenames)]
	row_num = result.shape[0]
	row_num = int(row_num)
	return_result = {'row_num': row_num, 'resultcookies': resultcookies}
	return return_result
# End of functions

# -- LOGIC -- Application logic
# Initial Unifi Login
resultcookies = login_unifi()
# Initial startup camera
sid = dsm_login()
dsm_enable_camera(sid)
dsm_logout(sid)

# Loop for checking
while True:
	found = check_unifi(resultcookies)
	resultcookies = found['resultcookies']
	if (found['row_num'] > 0):
		message(str(found['row_num']) + ' client(s) found (' + unifi_devicenames_text + ')')
		sid = dsm_login()
		dsm_disable_camera(sid)
		dsm_logout(sid)
		while (found['row_num'] > 0):
			time.sleep(polltime_found)
			found = check_unifi(resultcookies)
			resultcookies = found['resultcookies']
			print(str(found['row_num']) + ' client(s) still inside (' + unifi_devicenames_text + ')')
		message('Client(s) has left the building (' + unifi_devicenames_text + ')')
		sid = dsm_login()
		dsm_enable_camera(sid)
		dsm_logout(sid)
	else:
		print('Nothing to do, result: ' + str(found['row_num']))
	time.sleep(polltime_away)