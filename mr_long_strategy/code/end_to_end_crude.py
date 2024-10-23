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
from datetime import datetime
import  functools

from aws_calculate_BB_RSI import rsi_2, bollinger_band,symbol_lookup,get_nearest_expiry
from aws_place_order import place_robo_order


TOTP("").now()

with open('C:\git\mr_long_strategy\mr_long_strategy\config.json', 'r') as config_file:
    config = json.load(config_file)


key_path = config['key_path']
key_secret_file = config['key_secret_file']
instrument_url = config['instrument_url']
output_file_path = config['output_file_path']

#os.chdir(key_path)
key_secret = open(key_secret_file, "r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_file = "instrument_list.json"
placed_order_id = 0
if os.path.exists(instrument_file):
    with open(instrument_file, "r") as f:
        instrument_list = json.load(f)
    print("Instrument list loaded from cache")
else:
    instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    print("Fetching instrument list")
    response = urllib.request.urlopen(instrument_url)
    instrument_list = json.loads(response.read())
    with open(instrument_file, "w") as f:
        json.dump(instrument_list, f)
    print("Instrument list fetched and cached")

nearest_expiry =  get_nearest_expiry(config['symbol'], instrument_list)
print(nearest_expiry)
exchange, symbol,expiry = symbol_lookup(config['token'], instrument_list)
today = dt.date.today()

def get_nearest_exp():
    today = dt.date.today()
    # Calculate the number of days until the next Wednesday
    days_until_next_wednesday = (2 - today.weekday()) % 7

    # Add the days to today's date to get the next Wednesday
    next_wednesday = today + dt.timedelta(days=days_until_next_wednesday)
    nearest_exp = next_wednesday.strftime("%d%b%y")
    return nearest_exp.upper()
expiry=get_nearest_exp()
#print("Expiry date:", expiry )

# Get Strike Price to select options
def get_strike_price():
    #temp =pd.read_csv(output_file_path + str(today) + '.csv')
    #temp.columns=['date', 'open', 'high', 'low', 'close', 'volume']
    # exchange, symbol = symbol_lookup(config['token'], instrument_list)
    price = obj.ltpData(exchange,symbol, config['token'])['data']['ltp']
    remainder = price % 50
    if remainder <= 25:
        strike = price - remainder
    else:
        strike = price + (50 - remainder)
    return int(strike)
    
def token_lookup(strike_symbol, instrument_list, exchange="MCX"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol :
         return instrument["token"]


def hist_data(token,interval,st_date,end_date,instrument_list,exchange="MCX"):
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": st_date,
        "todate": end_date,
    }
    hist_data = obj.getCandleData(params)
    df_data = pd.DataFrame(hist_data["data"],
                           columns = ["date","open","high","low","close", "volume"])
    df_data.set_index("date",inplace=True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.index = df_data.index.tz_localize(None)
    return df_data

def lot_number(strike_symbol,token, exchange=config['exchange'], fund_in=config['capital_in']):
    ltp = obj.ltpData(exchange,strike_symbol, token)['data']['ltp']
    lot_num = int(fund_in/(ltp*25))
    return lot_num

def fetch_1_min_data_and_place_order(strike_symbol, token, st_date_1min, end_date_1min, high, entry_price, low):
    candle_df_1min = hist_data(token, "ONE_MINUTE", st_date_1min, end_date_1min, instrument_list)
    close_price = candle_df_1min["close"].iloc[-2]
    if close_price > high:
            lot = lot_number(strike_symbol,token)
            order_res = place_robo_order(strike_symbol, token, "BUY", entry_price, low, lot*100, instrument_list)
            print("order placed at price: ", entry_price)
            print("sl point is: ", entry_price - low)
            print("target point is: ", entry_price + 2*(entry_price - low))
                       
            global placed_order_id
            placed_order_id = order_res['data']['orderid']
    else:
        print("1min candle does not close above high of 5min candle")
        
        
def check_open_order():
    global placed_order_id
    response = obj.orderBook()   #response is a dict type
    order_book = pd.DataFrame(response["data"])
    #strike = [strike_symbol, strike_symbol]
    if order_book.empty:
        return False
    df = order_book[(order_book['status'] == 'trigger pending') & (order_book['parentorderid'] == placed_order_id) & (order_book['variety'] == 'ROBO')]
    if df.empty:
        return False  #currently no open order
    else:
        return True




def execute_strategy():
    if check_open_order() == False:

        
        strike_price = get_strike_price()
        print("Strike Price: ", strike_price)
        
        
        strike_symbol_CE = (config['symbol']+nearest_expiry+str(strike_price)+'CE').upper()
        strike_symbol_PE = (config['symbol']+nearest_expiry+str(strike_price)+'PE').upper()
        
        print(strike_symbol_CE)
        print(strike_symbol_PE)
        
        token_CE = token_lookup(strike_symbol_CE, instrument_list)
        token_PE = token_lookup(strike_symbol_PE, instrument_list)
        print(token_CE)
        print(token_PE)
        
        if today.weekday() == 0:
            yesterday = today - dt.timedelta(days=3)
        else:
            yesterday = today - dt.timedelta(days=1)
        
        st_date_5min = str(yesterday) + " 13:30"
        end_date_5min = str(today) + " 23:30"
        
        st_date_1min = str(today) + " 09:30"
        end_date_1min = str(today) + " 23:20"
        
        
        candle_df_ce_5min = hist_data(token_CE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)
        # print(candle_df)
        candle_df_pe_5min = hist_data(token_PE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)
        
        ce_temp_bb_df = bollinger_band(candle_df_ce_5min)
        pe_temp_bb_df = bollinger_band(candle_df_pe_5min)
        
        
        ce_bb = round(ce_temp_bb_df["UB"].iloc[-2], 2)
        pe_bb = round(pe_temp_bb_df["UB"].iloc[-2], 2)
        
        print("ce bb value: %d" %(ce_bb))
        print("pe bb value: %d" %(pe_bb))
        
        ce_temp_rsi_df = rsi_2(candle_df_ce_5min)
        pe_temp_rsi_df = rsi_2(candle_df_pe_5min)
        
        ce_rsi = round(ce_temp_rsi_df["rsi_2"].iloc[-2], 2)
        pe_rsi = round(pe_temp_rsi_df["rsi_2"].iloc[-2], 2)
        print("ce rsi value: %d" %(ce_rsi))
        print("pe rsi value: %d" %(pe_rsi))
        
        schedule.clear('ce_job')
        
        if candle_df_ce_5min["close"].iloc[-2] > ce_bb and ce_rsi > 60:
            # Get the current time
            current_time = datetime.now()
            current_minute = current_time.minute
        
            # Calculate the next 5-minute boundary
            #next_5min_boundary = current_minute + (5 - (current_minute % 5))
        
            # Define the function to be executed
            def schedule_until_next_block():
                current_time_inner = datetime.now()
                current_minute_inner = current_time_inner.minute
        
                # Stop scheduling after the next 5-minute block
                if (current_minute_inner >= current_minute +1) and (current_minute_inner % 5 == 0):
                    schedule.clear('ce_job')
                else:
                    fetch_1_min_data_and_place_order(strike_symbol_CE, token_CE, st_date_1min, end_date_1min, candle_df_ce_5min["high"].iloc[-2], candle_df_ce_5min["low"].iloc[-2])
        
        
            # Schedule the task every minute at 5 seconds
            schedule.every().minute.at(":05").do(lambda: schedule_until_next_block()).tag('ce_job')
        elif candle_df_pe_5min["close"].iloc[-2] > pe_bb and pe_rsi > 60:
            # Get the current time
            current_time = datetime.now()
            current_minute = current_time.minute
        
            # Calculate the next 5-minute boundary
            #next_5min_boundary = current_minute + (5 - (current_minute % 5))
             # Define the function to be executed
            def schedule_until_next_block():
                current_time_inner = datetime.now()
                current_minute_inner = current_time_inner.minute
        
                # Stop scheduling after the next 5-minute block
                if (current_minute_inner >= current_minute +1) and (current_minute_inner % 5 == 0):
                    schedule.clear('pe_job')
                else:
                    fetch_1_min_data_and_place_order(strike_symbol_PE, token_PE, st_date_1min, end_date_1min, candle_df_pe_5min["high"].iloc[-2], candle_df_pe_5min["low"].iloc[-2])
                    
            schedule.every().minute.at(":05").do(lambda: schedule_until_next_block()).tag('pe_job')
            
        else:
            print("5min candle did not close above BB")
        
        
        # Schedule the function to run every 5 minutes
for minute in range(0, 60, 5):
    schedule.every().hour.at(f":{minute:02d}").do(lambda: execute_strategy())


while True:
    schedule.run_pending()
    time.sleep(1)