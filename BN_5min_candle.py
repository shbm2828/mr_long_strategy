import pandas as pd
import time
import schedule
#from datetime import datetime
#from datetime import date
import datetime

today = datetime.date.today()
#today = datetime.date.today()
#today = str(date.today())


def BN_5min_candle():
    df = pd.read_csv('D:\\key\\mr_long_data\\BN_data\\BN_live_data_'+str(today)+'.csv', header=None)
    df.columns=['date', 'ltp']
    df['date'] = pd.to_datetime(df.date)  
    five_min_data = df.set_index('date').resample('5min').ohlc().reset_index()
    five_min_data.to_csv(r'D:\\key\\mr_long_data\\BN_data\\BN_5min_candle_'+str(today)+'.csv', header=None, index=False)
    #time.sleep(60)

schedule.every(5).minutes.do(BN_5min_candle)
while True:
    schedule.run_pending()
    time.sleep(5)
