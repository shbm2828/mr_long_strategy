import os
import urllib
from SmartApi import SmartConnect
from pyotp import TOTP
import json

TOTP("").now()
key_path = r"D:\key"
os.chdir(key_path)
key_secret = open("shbm_key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
print("Instrument list fetched")
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())




strike_symbol_CE = "BANKNIFTY16OCT2451800CE"
token_CE = 43745

def place_robo_order(strike_symbol_CE, token_CE, buy_sell, price, quantity, instrument_list, exchange='NFO'):
    params = {
        "variety": "ROBO",
        "tradingsymbol": strike_symbol_CE,
        "symboltoken": token_CE,
        "transactiontype": buy_sell,
        "exchange": exchange,
        "ordertype": "LIMIT",
        "producttype": "BO",
        "duration": "DAY",
        "price": price,
        "stoploss": 30,         #in point
        "squareoff": 60,           #in point
        "trailingstoploss": 10,         #in point
        "quantity": quantity        
        }
    response = obj.placeOrder(params)
    return response

place_robo_order(strike_symbol_CE, token_CE, "BUY", 235, 15, instrument_list)





