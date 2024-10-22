import functools
import schedule
import logging
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('demoOrder.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

orderPlaced = False

def place_order(token, entry, stoploss, st_date, end_date):
    global orderPlaced
    try:
        from aws_end_to_end_workflow import hist_data as hist_data_CE, instrument_list  # Adjust the import as needed

        trailStopLoss = entry + (entry - stoploss)
        logger.info("Trail stop loss: %s", trailStopLoss)
        bookProfit = entry + 2 * (entry - stoploss)
        logger.info("Book profit: %s", bookProfit)
        orderPrice = entry
        if not orderPlaced:
            logger.info("Order placed")
            orderPlaced = True

            stoploss_dict = {"value": stoploss}  # Use a dictionary to store stoploss

            def check_order(token, entry, stoploss_dict, st_date, end_date, trailStopLoss, bookProfit):
                global orderPlaced
                try:
                    candle_df = hist_data_CE(token, "ONE_MINUTE", st_date, end_date, instrument_list)
                    current_price = candle_df["close"].iloc[-1]
                    logger.info(f"Current price: {current_price}, token: {token}, entry: {entry}, stoploss: {stoploss_dict['value']}, st_date: {st_date}, end_date: {end_date}, trailStopLoss: {trailStopLoss}, bookProfit: {bookProfit}")
                    if current_price <= stoploss_dict["value"]:
                        logger.info("Stoploss hit")
                        orderPlaced = False
                        logger.info("Stoploss hit: %s rupees", (current_price - orderPrice) * 100)
                        schedule.clear('order_check')
                    elif current_price > bookProfit:
                        logger.info("Booking profit: %s rupees", (current_price - orderPrice) * 100)
                        orderPlaced = False
                        schedule.clear('order_check')  # Clear the scheduled job
                    elif current_price >= trailStopLoss:
                        logger.info("Trailing stop loss to entry value")
                        stoploss_dict["value"] = entry  # Update the stoploss value
                except Exception as e:
                    logger.error("Error in check_order: %s", e)

            # Schedule the check_order function to run every 1 minute
            schedule.every(1).minutes.do(
                functools.partial(check_order, token, entry, stoploss_dict, st_date, end_date, trailStopLoss, bookProfit)
            ).tag('order_check')
            logger.info("Scheduled order check")
        else:
            logger.info("Order already placed")
    except Exception as e:
        logger.error("Error in place_order: %s", e)

def fetch_1_min_data_CE(token_CE, st_date, end_date, high, low):
    try:
        from aws_end_to_end_workflow import hist_data as hist_data_CE, instrument_list  # Adjust the import as needed

        logger.info(
            f"Params - token_CE: {token_CE}, st_date: {st_date}, end_date: {end_date}, high: {high}, low: {low}, current_minute: {datetime.now().minute}")
        candle_df_ce_1 = hist_data_CE(token_CE, "ONE_MINUTE", st_date, end_date, instrument_list)
        close_price = candle_df_ce_1["close"].iloc[-1]
        if close_price > high:
            logger.info("High breached")
            place_order(token_CE, high, low, st_date, end_date)
        logger.info("Close price of 1-minute candle for CE: %s", close_price)
    except Exception as e:
        logger.error("Error in fetch_1_min_data_CE: %s", e)

def fetch_1_min_data_PE(token_PE, st_date, end_date):
    try:
        from aws_end_to_end_workflow import hist_data as hist_data_CE, instrument_list  # Adjust the import as needed

        candle_df_pe_1 = hist_data_CE(token_PE, "ONE_MINUTE", st_date, end_date, instrument_list)
        close_price = candle_df_pe_1["close"].iloc[-1]
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