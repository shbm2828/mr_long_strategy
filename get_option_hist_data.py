import os
import urllib
import json
import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
from pyotp import TOTP

TOTP("").now()
key_path = r"D:\key"
os.chdir(key_path)
key_secret = open("shbm_key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())

def get_nearest_exp():
    today = dt.date.today()
    # Calculate the number of days until the next Wednesday
    days_until_next_wednesday = (2 - today.weekday()) % 7

    # Add the days to today's date to get the next Wednesday
    next_wednesday = today + dt.timedelta(days=days_until_next_wednesday)
    nearest_exp = next_wednesday.strftime("%d%b%y")
    return nearest_exp

expiry=get_nearest_exp()

def token_lookup(ticker, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange and instrument["symbol"].split("-")[-1] == "EQ":
         return instrument["token"]
     
strike_symbol = 'BANKNIFTY'+expiry+'49300CE'

     
def token_lookup(strike, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol and instrument["exch_seg"] == exchange:
         return instrument["token"]
token = 44053

def hist_data(token, duration, interval, instrument_list, exchange="NSE"):

        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": interval,
            "fromdate": (dt.date.today() - dt.timedelta(duration)).strftime("%Y-%m-%d %H:%M"),
            "todate": dt.date.today().strftime("%Y-%m-%d %H:%M")
            }
                                               
        hist_data = obj.getCandleData(params)
        df_hist_data = pd.DataFrame(hist_data["data"],
                                    columns=["date", "open", "high", "low", "close", "volume"])
        df_hist_data.set_index("date",inplace=True)
        df_hist_data.index = pd.to_datetime(df_hist_data.index)
        df_hist_data.index = df_hist_data.index.tz_localize(None)
        #hist_tickers_data[ticker] = df_hist_data
        return df_hist_data

opt_hist_data = hist_data(token, 1, "ONE_MINUTE", instrument_list)

