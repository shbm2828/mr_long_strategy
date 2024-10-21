import pandas as pd
import numpy as np

#get option candle data


def bollinger_band(candle_df, n=20):
    candle_df["MB"] = candle_df["close"].rolling(n).mean()
    candle_df["UB"] = candle_df["MB"] + 2*candle_df["close"].rolling(n).std(ddof=0)
    candle_df["LB"] = candle_df["MB"] - 2*candle_df["close"].rolling(n).std(ddof=0)
    return candle_df


def EMA(candle_df, n=9):
    multiplier = 2/(n+1)    
    sma = candle_df.rolling(n).mean()
    ema = np.full(len(candle_df), np.nan)
    ema[len(sma) - len(sma.dropna())] = sma.dropna()[0]
    for i in range(len(candle_df)):
        if not np.isnan(ema[i-1]):
            ema[i] = ((candle_df.iloc[i] - ema[i-1])*multiplier) + ema[i-1]
    ema[len(sma) - len(sma.dropna())] = np.nan
    return ema


def RSI(candle_df, n=14):
    candle_df["change"] = candle_df["close"] - candle_df["close"].shift(1)
    candle_df["gain"] = np.where(candle_df["change"] >= 0, candle_df["change"], 0)
    candle_df["loss"] = np.where(candle_df["change"] < 0, -1*candle_df["change"], 0)
    candle_df["avg_gain"] = EMA(candle_df["gain"], n)
    candle_df["avg_loss"] = EMA(candle_df["loss"], n)
    candle_df["rs"] = candle_df["avg_gain"]/candle_df["avg_loss"]
    candle_df["rsi"] = 100 - (100/(1+candle_df["rs"]))
    candle_df.drop(["change", "gain", "loss", "avg_gain", "avg_loss", "rs"], axis=1, inplace=True)
    return candle_df

def symbol_lookup(token, instrument_list):
    for instrument in instrument_list:
        if instrument["token"] == token:
            exch_seg = instrument["exch_seg"]
            symbol = instrument["symbol"]
            expiry = instrument["expiry"]
            # Format expiry date to 19NOV24
            formatted_expiry = expiry[:-4] + expiry[-2:]
            return exch_seg, symbol, formatted_expiry

from datetime import datetime


def get_nearest_expiry(symbol, instrument_list):
    today = datetime.now()

    # Filter instruments by symbol
    matching_instruments = [instrument for instrument in instrument_list if instrument["name"] == symbol]

    if not matching_instruments:
        raise ValueError(f"No instruments found for symbol: {symbol}")

    # Extract expiry dates and convert them to datetime objects, ignoring empty expiry fields and past dates
    expiry_dates = [
        datetime.strptime(instrument["expiry"], "%d%b%Y")
        for instrument in matching_instruments
        if instrument["expiry"] and datetime.strptime(instrument["expiry"], "%d%b%Y") > today
    ]

    if not expiry_dates:
        raise ValueError(f"No valid future expiry dates found for symbol: {symbol}")

    # Find the nearest expiry date
    nearest_expiry = min(expiry_dates)

    # Format the nearest expiry date back to the original format
    formatted_expiry = nearest_expiry.strftime("%d%b%y")

    return formatted_expiry.upper()

#bollinger_band(candle_df)
#RSI(candle_df)

#print(candle_df)