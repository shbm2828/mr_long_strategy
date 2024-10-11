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

#from get_option_hist_data import strike_symbol_CE

#from calculate_BB_RSI import bollinger_band
#from get_option_hist_data import hist_data_PE

TOTP("").now()
key_path = r"C:\Users\HP\Desktop\mr_long_strategy"
os.chdir(key_path)
key_secret = open("key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_file = "instrument_list.json"

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
    temp = pd.read_csv('C:\\Users\\HP\\Desktop\\mr_long_strategy\\mr_long_data\\BN_data\\BN_5min_candle_'+str(today)+'.csv')
    temp.columns=['date', 'open', 'high', 'low', 'close']
    price = int(temp.iloc[-2]["close"])
    remainder = price % 100
    if remainder <= 50:
        strike = price - remainder
    else:
        strike = price + (100 - remainder)
    return strike
    
def token_lookup_CE(strike_symbol_CE, instrument_list, exchange="MCX"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_CE :
         return instrument["token"]


def token_lookup_PE(strike_symbol_PE, instrument_list, exchange="MCX"):
    for instrument in instrument_list:
        if instrument["symbol"] == strike_symbol_PE :
         return instrument["token"]

def hist_data_CE(token_CE,interval,st_date,end_date,instrument_list,exchange="MCX"):
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
    print(
        f"Params - token_CE: {token_CE}, st_date: {st_date}, end_date: {end_date}, high: {high}, low: {low}, current_minute: {datetime.now().minute}")
    candle_df_ce_1 = hist_data_CE(token_CE, "ONE_MINUTE", st_date, end_date, instrument_list)
    close_price = candle_df_ce_1["close"].iloc[-1]
    if close_price > high:
        print("High breached")
        place_order(token_CE, high, low, st_date, end_date)
    print(f"Close price of 1-minute candle for CE: {close_price}")

def fetch_1_min_data_PE(token_PE, st_date, end_date):
    candle_df_pe_1 = hist_data_CE(token_PE, "ONE_MINUTE", st_date, end_date, instrument_list)
    close_price = candle_df_pe_1["close"].iloc[-1]
    print(f"Close price of 1-minute candle for PE: {close_price}")


def place_order(token, entry, stoploss, st_date, end_date):
    global orderPlaced
    trailStopLoss = entry + (entry - stoploss)
    print("Trail stop loss: ", trailStopLoss)
    bookProfit = entry + 2 * (entry - stoploss)
    print("Book profit: ", bookProfit)
    orderPrice = entry
    if not orderPlaced:
        print("Order placed")
        orderPlaced = True

        stoploss_dict = {"value": stoploss}  # Use a dictionary to store stoploss

        def check_order(token, entry, stoploss_dict, st_date, end_date, trailStopLoss, bookProfit):
            global orderPlaced
            candle_df = hist_data_CE(token, "ONE_MINUTE", st_date, end_date, instrument_list)
            current_price = candle_df["close"].iloc[-1]
            print(f"Current price: {current_price}, token: {token}, entry: {entry}, stoploss: {stoploss_dict['value']}, st_date: {st_date}, end_date: {end_date}, trailStopLoss: {trailStopLoss}, bookProfit: {bookProfit}")
            if current_price <= stoploss_dict["value"]:
                print("Stoploss hit")
                orderPlaced = False
                print("Stoploss hit", (current_price - orderPrice) * 100, "rupees")
                schedule.clear('order_check')
            elif current_price > bookProfit:
                print("Booking profit", (current_price - orderPrice) * 100, "rupees")
                orderPlaced = False
                schedule.clear('order_check')  # Clear the scheduled job
            elif current_price >= trailStopLoss:
                print("Trailing stop loss to entry value")
                stoploss_dict["value"] = entry  # Update the stoploss value

        # Schedule the check_order function to run every 1 minute
        schedule.every(1).minutes.do(
            functools.partial(check_order, token, entry, stoploss_dict, st_date, end_date, trailStopLoss, bookProfit)
        ).tag('order_check')
        print("Scheduled order check")
    else:
        print("Order already placed")




#strike_price = 51300


# Function to execute every 5 minutes
def execute_strategy():
    global orderPlaced

    strike_price = get_strike_price()
    print("Strike Price: ", strike_price)

    strike_symbol_CE = ('CRUDEOIL17OCT24' + str(strike_price) + 'CE').upper()
    strike_symbol_PE = ('CRUDEOIL17OCT24' + str(strike_price) + 'PE').upper()

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

    st_date = str(today) + " 09:30"
    end_date = str(today) + " 23:30"

    candle_df = hist_data_CE(token_CE, "FIVE_MINUTE", st_date, end_date, instrument_list)
    # print(candle_df)
    candle_pe_df = hist_data_CE(token_PE, "FIVE_MINUTE", st_date, end_date, instrument_list)

    ce_bb = 'buy'  # bollinger_band(candle_df)
    ce_rsi = 60

    pe_bb = 'notBuy'  # bollinger_band(candle_pe_df)
    pe_rsi = 60

    schedule.clear('ce_job')

    if ce_bb == "buy" and ce_rsi > 50 and not orderPlaced:
        print(strike_symbol_CE + " is a Buy")

        # Get the current time
        current_time = datetime.now()
        current_minute = current_time.minute

        # Calculate the next 5-minute boundary
        next_5min_boundary = current_minute + (5 - (current_minute % 5))

        # Define the function to be executed
        def schedule_until_next_block():
            current_time_inner = datetime.now()
            current_minute_inner = current_time_inner.minute

            # Stop scheduling after the next 5-minute block
            if (current_minute_inner >= current_minute +1) and (current_minute_inner % 5 == 0):
                print(f"Reached next 5-minute boundary: {current_time_inner.strftime('%H:%M')}, stopping the job.")
                schedule.clear('ce_job')
            else:
                # Call the fetch method
                fetch_1_min_data_CE(token_CE, st_date, end_date, candle_df["high"].iloc[-2], candle_df["low"].iloc[-2])
                print(f"Data fetched at {current_time_inner.strftime('%H:%M:%S')}")

        # Schedule the task every minute at 5 seconds
        schedule.every().minute.at(":05").do(lambda: schedule_until_next_block() if not orderPlaced else None).tag('ce_job')
    elif pe_bb == "buy" and pe_rsi > 50 and not orderPlaced:
        print(strike_symbol_PE + " is a Buy")
        for i in range(1, 5):
            schedule.every().minute.at(f":{5 * i:02d}").do(
                lambda: fetch_1_min_data_PE(token_PE, st_date, end_date)
            )
    else:
        orderPlaced = False  # Ensure it's reset if no orders are placed


# Schedule the function to run every 5 minutes
for minute in range(0, 60, 5):
    schedule.every().hour.at(f":{minute:02d}").do(lambda: execute_strategy() if not orderPlaced else None)


while True:
    schedule.run_pending()
    time.sleep(1)






