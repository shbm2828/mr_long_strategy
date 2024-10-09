


def bollinger_band(candle_df, n=20):
    candle_df["MB"] = candle_df["close"].rolling(n).mean()
    candle_df["UB"] = candle_df["MB"] + 2*candle_df["close"].rolling(n).std(ddof=0)
    candle_df["LB"] = candle_df["MB"] - 2*candle_df["close"].rolling(n).std(ddof=0)
    

bollinger_band(candle_df)
    
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
a = EMA(candle_df)

if candle_df["close"].iloc[-1] > candle_df["UB"].iloc[-1]:
    print("take entry")


