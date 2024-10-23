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
import functools
from aws_calculate_BB_RSI import RSI, bollinger_band, symbol_lookup, get_nearest_expiry
from aws_place_order import place_robo_order
from demoOrder import fetch_1_min_data_CE, fetch_1_min_data_PE, check_demo_open_order
import logging

from mr_long_strategy.code.aws_calculate_BB_RSI import rsi_2

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('aws_end_to_end_workflow.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

try:
    TOTP("").now()
    # Get the directory of the current script
    script_dir = os.path.dirname(__file__)

    # Construct the path to config.json relative to the script directory
    config_path = os.path.join(script_dir, '..', '..', 'config.json')

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    key_path = config['key_path']
    key_secret_file = config['key_secret_file']
    instrument_url = config['instrument_url']
    output_file_path = config['output_file_path']

    os.chdir(key_path)
    key_secret = open(key_secret_file, "r").read().split()
    obj = SmartConnect(api_key=key_secret[0])
    data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

    instrument_file = "instrument_list.json"
    placed_order_id = 0
    if os.path.exists(instrument_file):
        with open(instrument_file, "r") as f:
            instrument_list = json.load(f)
        logger.info("Instrument list loaded from cache")
    else:
        instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        logger.info("Fetching instrument list")
        response = urllib.request.urlopen(instrument_url)
        instrument_list = json.loads(response.read())
        with open(instrument_file, "w") as f:
            json.dump(instrument_list, f)
        logger.info("Instrument list saved to cache")

    nearest_expiry = get_nearest_expiry(config['symbol'], instrument_list)
    logger.info("Nearest expiry: %s", nearest_expiry)
    exchange, symbol, expiry = symbol_lookup(config['token'], instrument_list)
    today = dt.date.today()

    def get_nearest_exp():
        today = dt.date.today()
        days_until_next_wednesday = (2 - today.weekday()) % 7
        next_wednesday = today + dt.timedelta(days=days_until_next_wednesday)
        nearest_exp = next_wednesday.strftime("%d%b%y")
        return nearest_exp

    def get_strike_price():
        try:
            price = obj.ltpData(exchange, symbol, config['token'])['data']['ltp']
            remainder = price % 100
            if remainder <= 50:
                strike = price - remainder
            else:
                strike = price + (100 - remainder)
            return int(strike)
        except Exception as e:
            logger.error("Error in get_strike_price: %s", e)
            return None


    def get_strike_price_nifty():
        try:
            price = obj.ltpData(exchange, symbol, config['token'])['data']['ltp']
            remainder = price % 50
            if remainder <= 25:
                strike = price - remainder
            else:
                strike = price + (50 - remainder)
            return int(strike)
        except Exception as e:
            logger.error("Error in get_strike_price: %s", e)
            return None

    def token_lookup(strike_symbol, instrument_list, exchange="NFO"):
        try:
            for instrument in instrument_list:
                if instrument["symbol"] == strike_symbol:
                    return instrument["token"]
        except Exception as e:
            logger.error("Error in token_lookup: %s", e)
            return None

    def hist_data(token, interval, st_date, end_date, instrument_list, exchange="NFO"):
        try:
            params = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": st_date,
                "todate": end_date,
            }
            hist_data = obj.getCandleData(params)
            df_data = pd.DataFrame(hist_data["data"],
                                   columns=["date", "open", "high", "low", "close", "volume"])
            df_data.set_index("date", inplace=True)
            df_data.index = pd.to_datetime(df_data.index)
            df_data.index = df_data.index.tz_localize(None)
            return df_data
        except Exception as e:
            logger.error("Error fetching historical data: %s", e)
            return pd.DataFrame()

    def fetch_1_min_data_and_place_order(strike_symbol, token, st_date_1min, end_date_1min, high, low):
        try:
            candle_df_1min = hist_data(token, "ONE_MINUTE", st_date_1min, end_date_1min, instrument_list)
            logger.debug("1min candle data: %s", candle_df_1min)
            close_price = candle_df_1min["close"].iloc[-2]
            logger.info("Close price: %d", close_price)
            if close_price > high:
                logger.info("Close price is greater than high")
                order_res = place_robo_order(strike_symbol, token, "BUY", high, 15, instrument_list)
                global placed_order_id
                placed_order_id = order_res['data']['orderid']
        except Exception as e:
            logger.error("Error in fetch_1_min_data_and_place_order: %s", e)

    def check_open_order():
        global placed_order_id
        try:
            response = obj.orderBook()
            logger.debug("Order book: %s", response)
            order_book = pd.DataFrame(response["data"])
            if order_book.empty:
                return False
            df = order_book[(order_book['status'] == 'trigger pending') & (order_book['parentorderid'] == placed_order_id) & (order_book['variety'] == 'ROBO')]
            if df.empty:
                return False
            else:
                return True
        except Exception as e:
            logger.error("Error checking open order: %s", e)
            return False

    def execute_strategy():
        try:
            logger.info(check_demo_open_order())
            if check_demo_open_order() == False:
                strike_price = get_strike_price_nifty()
                if strike_price is None:
                    return
                logger.info("Strike price: %d", strike_price)

                strike_symbol_CE = (config['symbol'] + nearest_expiry + str(strike_price) + 'CE').upper()
                strike_symbol_PE = (config['symbol'] + nearest_expiry + str(strike_price) + 'PE').upper()

                logger.info("Strike symbol CE: %s", strike_symbol_CE)
                logger.info("Strike symbol PE: %s", strike_symbol_PE)

                token_CE = token_lookup(strike_symbol_CE, instrument_list)
                token_PE = token_lookup(strike_symbol_PE, instrument_list)
                if token_CE is None or token_PE is None:
                    return
                logger.info("Token CE: %s", token_CE)
                logger.info("Token PE: %s", token_PE)

                if today.weekday() == 0:
                    yesterday = today - dt.timedelta(days=3)
                else:
                    yesterday = today - dt.timedelta(days=1)

                st_date_5min = str(yesterday) + " 13:30"
                end_date_5min = str(today) + " 23:30"

                st_date_1min = str(today) + " 09:30"
                end_date_1min = str(today) + " 23:30"

                candle_df_ce_5min = hist_data(token_CE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)
                candle_df_pe_5min = hist_data(token_PE, "FIVE_MINUTE", st_date_5min, end_date_5min, instrument_list)

                ce_temp_bb_df = bollinger_band(candle_df_ce_5min)
                pe_temp_bb_df = bollinger_band(candle_df_pe_5min)

                ce_bb = round(ce_temp_bb_df["UB"].iloc[-2], 2)
                logger.info("CE BB value: %d", ce_bb)
                pe_bb = round(pe_temp_bb_df["UB"].iloc[-2], 2)
                logger.info("PE BB value: %d", pe_bb)

                ce_temp_rsi_df = rsi_2(candle_df_ce_5min)
                pe_temp_rsi_df = rsi_2(candle_df_pe_5min)

                ce_rsi = round(ce_temp_rsi_df["rsi_2"].iloc[-2], 2)
                logger.info("CE RSI value: %d", ce_rsi)
                pe_rsi = round(pe_temp_rsi_df["rsi_2"].iloc[-2], 2)
                logger.info("PE RSI value: %d", pe_rsi)


                schedule.clear('ce_job')
                schedule.clear('pe_job')

                if candle_df_ce_5min["close"].iloc[-2] > ce_bb or ce_rsi > 60:
                    logger.info("5min CE candle closed above BB and RSI > 60")
                    current_time = datetime.now()
                    current_minute = current_time.minute

                    def schedule_ce_1_min():
                        current_time_inner = datetime.now()
                        logger.info("Current time: %s", current_time_inner)
                        current_minute_inner = current_time_inner.minute
                        logger.info("Current minute: %s", current_minute_inner)

                        if (current_minute_inner >= current_minute + 1) and (current_minute_inner % 5 == 0):
                            schedule.clear('ce_job')
                        else:
                            fetch_1_min_data_CE(token_CE, st_date_1min, end_date_1min, candle_df_ce_5min["high"].iloc[-2], candle_df_ce_5min["low"].iloc[-2])
                    schedule.every().minute.at(":05").do(lambda: schedule_ce_1_min()).tag('ce_job')
                elif candle_df_pe_5min["close"].iloc[-2] > pe_bb and pe_rsi > 60:
                    logger.info("5min PE candle closed above BB and RSI > 60")
                    current_time = datetime.now()
                    logger.info("Current time: %s", current_time)
                    current_minute = current_time.minute
                    logger.info("Current minute: %s", current_minute)

                    def schedule_pe_1_min():
                        current_time_inner = datetime.now()
                        current_minute_inner = current_time_inner.minute

                        if (current_minute_inner >= current_minute + 1) and (current_minute_inner % 5 == 0):
                            schedule.clear('pe_job')
                        else:
                            fetch_1_min_data_PE(token_PE, st_date_1min, end_date_1min, candle_df_pe_5min["high"].iloc[-2], candle_df_pe_5min["low"].iloc[-2])
                    schedule.every().minute.at(":05").do(lambda: schedule_pe_1_min()).tag('pe_job')
                else:
                    logger.info("No trade signal")
        except Exception as e:
            logger.exception("Error in execute_strategy: %s", e)

    for minute in range(0, 60,5 ):
        schedule.every().hour.at(f":{minute:02d}").do(lambda: execute_strategy())

    while True:
        schedule.run_pending()
        time.sleep(1)
except Exception as e:
    logger.error("Error in main workflow: %s", e)
    raise

