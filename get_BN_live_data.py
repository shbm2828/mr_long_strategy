from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect
import os
import urllib
import json
from pyotp import TOTP
import csv
from datetime import datetime
from datetime import date

global token
today = str(date.today())

TOTP("").now()
key_path = r"D:\key"
os.chdir(key_path)
key_secret = open("shbm_key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())
feed_token = obj.getfeedToken()

instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())

sws = SmartWebSocketV2(data["data"]["jwtToken"], key_secret[0], key_secret[2], feed_token, 3)

correlation_id = "BN_live_data"
action = 1
mode = 1
token_list = [{"exchangeType": 1, "tokens": [key_secret[5]]}]   #48200 CE
global LIVE_FEED_JSON

def on_open(wsapp): 
	print("on open")
	sws.subscribe(correlation_id, mode, token_list)

def on_data(wsapp, message):
    try:
        with open('mr_long_data\\BN_data\\BN_live_data_'+today+'.csv', 'a', newline='') as csvfile:
              writer = csv.writer(csvfile)
              writer.writerow([datetime.fromtimestamp(message['exchange_timestamp']/1000)
                               .isoformat(), message["last_traded_price"]/100])
        csvfile.close()
    except Exception as e:
        print(e)

def on_error(wsapp, error):
    print(error)

	
	
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error

sws.connect()
