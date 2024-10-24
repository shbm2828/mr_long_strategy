import functools
import schedule
import logging
import os
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('aws_place_order.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Get the directory of the current script
script_dir = os.path.dirname("C:\git\mr_long_strategy\mr_long_strategy\code")

# Construct the path to config.json relative to the script directory
config_path = os.path.join(script_dir, 'config.json')

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

key_path = config['key_path']
key_secret_file = config['key_secret_file']
instrument_url = config['instrument_url']
output_file_path = config['output_file_path']


orderPlaced = False

global lot_numbe
global check_open_order
global place_angle_robo_order


def lot_number(strike_symbol,token, exchange=config['exchange'], fund_in=config['capital_in']):
    ltp = obj.ltpData(exchange,strike_symbol, token)['data']['ltp']
    lot_num = int(fund_in/(ltp*25))
    return lot_num, ltp


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




def place_angle_robo_order(strike_symbol, token, buy_sell, entry_price, low, quantity, instrument_list, exchange='NFO'):
    params = {
        "variety": "ROBO",
        "tradingsymbol": strike_symbol,
        "symboltoken": token,
        "transactiontype": buy_sell,
        "exchange": exchange,
        "ordertype": "LIMIT",
        "producttype": "BO",
        "duration": "DAY",
        "price": entry_price,
        "stoploss": entry_price - low,         #in point
        "squareoff": 2*(entry_price - low),           #in point
        "trailingstoploss": entry_price - low,         #in point
        "quantity": quantity        
        }
    response = obj.placeOrder(params) # obj.placeOrder(params)
    return response




def fetch_1_min_data_CE(strike_symbol_CE, token_CE, st_date, end_date, high, low):
    try:
        from aws_end_to_end_workflow import hist_data as hist_data_CE, instrument_list as instrument_list

        logger.info(
            f"Params - token_CE: {token_CE}, st_date: {st_date}, end_date: {end_date}, high: {high}, low: {low}, current_minute: {datetime.now().minute}")
        candle_df_ce_1 = hist_data_CE(token_CE, "ONE_MINUTE", st_date, end_date, instrument_list)
        close_price = candle_df_ce_1["close"].iloc[-1]
        if close_price > high:
            logger.info("High breached")
            if check_open_order() == False:
                lot, ltp = lot_number(strike_symbol_CE, token_CE)
                order_res = place_angle_robo_order(strike_symbol_CE, token_CE, "buy", ltp, low, lot*25, instrument_list, exchange='NFO')
                logger.info(order_res)
            else:
                logger.info("order is already placed")
        logger.info("Close price of 1-minute candle for CE: %s", close_price)
    except Exception as e:
        logger.error("Error in fetch_1_min_data_CE: %s", e)





def fetch_1_min_data_PE(strike_symbol_PE, token_PE, st_date, end_date, high, low):
    try:
        from aws_end_to_end_workflow import hist_data as hist_data_PE, instrument_list as instrument_list

        logger.info(
            f"Params - token_PE: {token_PE}, st_date: {st_date}, end_date: {end_date}, high: {high}, low: {low}, current_minute: {datetime.now().minute}")
        candle_df_pe_1 = hist_data_PE(token_PE, "ONE_MINUTE", st_date, end_date, instrument_list)
        close_price = candle_df_pe_1["close"].iloc[-1]
        if close_price > high:
            logger.info("High breached")
            if check_open_order() == False:
                lot, ltp = lot_number(strike_symbol_PE, token_PE)
                order_res = place_angle_robo_order(strike_symbol_PE, token_PE, "buy", ltp, low, lot*25, instrument_list, exchange='NFO')
                logger.info(order_res)
            else:
                logger.info("order already placed")
        logger.info("Close price of 1-minute candle for PE: %s", close_price)
    except Exception as e:
        logger.error("Error in fetch_1_min_data_PE: %s", e)
def check_demo_open_order():
    global orderPlaced
    try:
        return orderPlaced
    except Exception as e:
        logger.error("Error in check_demo_open_order: %s", e)
        return False




