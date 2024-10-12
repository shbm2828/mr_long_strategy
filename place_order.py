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

def token_lookup(strike_symbol_CE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_CE :
         return instrument["token"]



def symbol_lookup(token_CE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["token"] == token_CE and instrument["exch_seg"] == exchange:
            return(instrument["symbol"])



def place_limit_order(strike_symbol, token, buy_sell, price, quantity, instrument_list, exchange="NSE"):
    
    params = {
        "variety": "NORMAL",
        "tradingsymbol": strike_symbol,
        "symboltoken": token,
        "transactiontype": buy_sell,
        "exchange": "NSE",
        "ordertype": "LIMIT",
        "producttype": "INTRADAY",
        "duration": "DAY",
        "price": price,
        "quantity": quantity
        }
    order = obj.placeOrder(params)
    print(order)
    
    
    
def place_robo_order(instrument_list, ticker, buy_sell, price, quantity, exchange='NSE'):
    params = {
        "varity": "ROBO",
        "trdingsymbol": "{}-EQ".format(ticker),
        "symboletoken": token_lookup(ticker, instrument_list),
        "exchange": exchange,
        "ordertype": "LIMIT",
        "producttype": "ROBO",
        "duration": "DAY",
        "price": price,
        "stoploss": price-30,
        "squareoff": price+60,
        "quantity": quantity        
        #"trailingstoploss": value
        }
    response = obj.placeOrder(params)
    return response

place_robo_order(instrument_list, 'HDFC', 'BUY', 400, 1)