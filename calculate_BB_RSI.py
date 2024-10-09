import pandas as pd
import numpy as np
import tempo

candle_df = tempo.candle_data   #get option candle data


def bollinger_band(candle_df, n=20):
    candle_df["MB"] = candle_df["close"].rolling(n).mean()
    candle_df["UB"] = candle_df["MB"] + 2*candle_df["close"].rolling(n).std(ddof=0)
    candle_df["LB"] = candle_df["MB"] - 2*candle_df["close"].rolling(n).std(ddof=0)


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

bollinger_band(candle_df)
RSI(candle_df)

print(candle_df)