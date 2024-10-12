import os
import urllib
import json
import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
from pyotp import TOTP
import schedule
import time
import numpy as np

TOTP("").now()
key_path = r"D:\key"
os.chdir(key_path)
key_secret = open("shbm_key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())

today = dt.date.today()




def get_nearest_exp():
    today = dt.date.today()
    # Calculate the number of days until the next Wednesday
    days_until_next_wednesday = (2 - today.weekday()) % 7

    # Add the days to today's date to get the next Wednesday
    next_wednesday = today + dt.timedelta(days=days_until_next_wednesday)
    nearest_exp = next_wednesday.strftime("%d%b%y")
    return nearest_exp
expiry=get_nearest_exp()

# Get Strike Price to select options
def get_strike_price():
    temp = pd.read_csv('D:\\key\\mr_long_data\\BN_data\\BN_hist_5min_candle_'+str(today)+'.csv')
    temp.columns=['date', 'open', 'high', 'low', 'close', 'volume']
    price = int(temp.iloc[-2]["close"])
    remainder = price % 100
    if remainder <= 50:
        strike = price - remainder
    else:
        strike = price + (100 - remainder)
    return strike
    
strike_price = get_strike_price()
#strike_price = 51300
     
strike_symbol_CE = ('BANKNIFTY'+expiry+str(strike_price)+'CE').upper()
strike_symbol_PE = ('BANKNIFTY'+expiry+str(strike_price)+'PE').upper()
print(strike_symbol_CE)
print(strike_symbol_PE)

     
def token_lookup_CE(strike_symbol_CE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_CE :
         return instrument["token"]
     
     
def token_lookup_PE(strike_symbol_PE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_PE :
         return instrument["token"]
     
token_CE = token_lookup_CE(strike_symbol_CE, instrument_list)
token_PE = token_lookup_PE(strike_symbol_PE, instrument_list)
print(token_CE)
print(token_PE)

if today.weekday() == 0:
    # If Monday, subtract 3 days to get the previous Friday
    yesterday = today - dt.timedelta(days=3)
else:
    # If not Monday, subtract 1 day to get the previous day
    yesterday = today - dt.timedelta(days=1)

st_date = str(yesterday) + " 13:30"
end_date = str(today) + " 15:30"



def hist_data_CE(token_CE,interval,st_date,end_date,instrument_list,exchange="NFO"):
    params = {
             "exchange": exchange,
             "symboltoken": token_CE,
             "interval": interval,
             "fromdate": st_date,
             "todate": end_date,
             }
    hist_data = obj.getCandleData(params)
    df_data = pd.DataFrame(hist_data["data"],
                           columns = ["date","open","high","low","close","volume"])
    df_data.set_index("date",inplace=True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.index = df_data.index.tz_localize(None)
    return df_data
        
  
candle_data = hist_data_CE(token_CE,"FIVE_MINUTE",st_date, end_date, instrument_list)






