import pandas as pd
import datetime

today = datetime.date.today()
def get_strike_price():
    temp = pd.read_csv('D:\\key\\mr_long_data\\BN_data\\BN_5min_candle_'+str(today)+'.csv')
    temp.columns=['date', 'open', 'high', 'low', 'close']
    price = int(temp.iloc[-2]["close"])
    remainder = price % 100
    if remainder <= 50:
        strike = price - remainder
    else:
        strike = price + (100 - remainder)
    return strike
    
strike_price = get_strike_price()
print(strike_price)


