import os
import urllib
import json
import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
from pyotp import TOTP

TOTP("").now()
key_path = r"D:\key"
os.chdir(key_path)
key_secret = open("shbm_key.txt","r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
response = urllib.request.urlopen(instrument_url)
instrument_list = json.loads(response.read())


today = dt.date.today()
st_date = str(today) + " 09:15"
end_date = str(today) + " 15:30"

def BN_hist_data(token,interval,st_date,end_date,instrument_list,exchange="NSE"):
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
    df_data.to_csv(r'D:\\key\\mr_long_data\\BN_data\\BN_hist_5min_candle_'+str(today)+'.csv')

BN_hist_data("99926009","FIVE_MINUTE",st_date, end_date, instrument_list)


