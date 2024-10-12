import os
import urllib
import json
from xmlrpc.client import boolean

import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
from pyotp import TOTP
import schedule
import time

from calculate_BB_RSI import EMA, RSI, bollinger_band

#from get_option_hist_data import strike_symbol_CE

#from calculate_BB_RSI import bollinger_band
#from get_option_hist_data import hist_data_PE

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

today = dt.date.today()

orderPlaced =  False



def get_nearest_exp():
    today = dt.date.today()
    # Calculate the number of days until the next Wednesday
    days_until_next_wednesday = (2 - today.weekday()) % 7

    # Add the days to today's date to get the next Wednesday
    next_wednesday = today + dt.timedelta(days=days_until_next_wednesday)
    nearest_exp = next_wednesday.strftime("%d%b%y")
    return nearest_exp
expiry=get_nearest_exp()
print("Expiry date:", expiry )

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
    
def token_lookup_CE(strike_symbol_CE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_CE :
         return instrument["token"]


def token_lookup_PE(strike_symbol_PE, instrument_list, exchange="NFO"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_PE :
         return instrument["token"]

def hist_data(token_CE,interval,st_date,end_date,instrument_list,exchange="NFO"):
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

def fetch_1_min_data_CE(token_CE, st_date, end_date, high, low):
    candle_df_ce_1min = hist_data(token_CE, "ONE_MINUTE", st_date, end_date, instrument_list)
    close_price = candle_df_ce_1min["close"].iloc[-1]
    if close_price > high:
        print("High breached")
        orderPlaced = True
    print(f"Close price of 1-minute candle for CE: {close_price}")

def fetch_1_min_data_PE(token_PE, st_date, end_date):
    candle_df_pe_1 = hist_data(token_PE, "ONE_MINUTE", st_date, end_date, instrument_list)
    close_price = candle_df_pe_1["close"].iloc[-1]
    print(f"Close price of 1-minute candle for PE: {close_price}")

#strike_price = 51300


# Function to execute every 5 minutes
def execute_strategy():
    global orderPlaced

    strike_price = get_strike_price()
    print("Strike Price: ", strike_price)

    strike_symbol_CE = ('BANKNIFTY'+expiry+str(strike_price)+'CE').upper()
    strike_symbol_PE = ('BANKNIFTY'+expiry+str(strike_price)+'PE').upper()
    
    print(strike_symbol_CE)
    print(strike_symbol_PE)


    token_CE = token_lookup_CE(strike_symbol_CE, instrument_list)
    token_PE = token_lookup_PE(strike_symbol_PE, instrument_list)
    print(token_CE)
    print(token_PE)


    if today.weekday() == 0:
        yesterday = today - dt.timedelta(days=3)
    else:
        yesterday = today - dt.timedelta(days=1)

    st_date_5min = str(yesterday) + " 13:30"
    end_date_5min = str(today) + " 15:30"

    st_date_1min = str(today) + " 09:30"
    end_date_1min = str(today) + " 15:30"

    candle_df_ce_5min = hist_data(token_CE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)
    candle_df_pe_5min = hist_data(token_PE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)

    ce_temp_bb_df = bollinger_band(candle_df_ce_5min)
    pe_temp_bb_df = bollinger_band(candle_df_pe_5min)

    
    ce_bb = round(ce_temp_bb_df["UB"].iloc[-1], 2)
    pe_bb = round(pe_temp_bb_df["UB"].iloc[-1], 2)
    
    print(ce_bb)
    print(pe_bb)
    
    ce_temp_rsi_df = RSI(candle_df_ce_5min)
    pe_temp_rsi_df = RSI(candle_df_pe_5min)
    
    ce_rsi = round(ce_temp_rsi_df["rsi"].iloc[-1], 2)
    pe_rsi = round(pe_temp_rsi_df["rsi"].iloc[-1], 2)
    print(ce_rsi)
    print(pe_rsi)
        

    if ce_bb > candle_df_ce_5min["high"].iloc[-1]  and ce_rsi > 60 and not orderPlaced:
        print(strike_symbol_CE + " is a Buy")
        for i in range(1, 5):
            schedule.every().minute.at(f":{5 * i:02d}").do(
                lambda: fetch_1_min_data_CE(token_CE,st_date_1min,end_date_1min,candle_df_ce_5min["high"].iloc[-1], candle_df_ce_5min["low"].iloc[-1]))
            print(orderPlaced)
    elif pe_bb == "buy" and pe_rsi > 50 and not orderPlaced:
        print(strike_symbol_PE + " is a Buy")
        for i in range(1, 5):
            schedule.every().minute.at(f":{5 * i:02d}").do(
                lambda: fetch_1_min_data_PE(token_PE, st_date_1min, end_date_1min)
            )
    else:
        orderPlaced = False  # Ensure it's reset if no orders are placed


# Schedule the function to run every 5 minutes
schedule.every(1).minutes.at(":00").do(execute_strategy)

while True:
    schedule.run_pending()
    time.sleep(1)