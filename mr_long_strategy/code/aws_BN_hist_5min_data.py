import os
import urllib
import json
import pandas as pd
import datetime as dt
from SmartApi import SmartConnect
from pyotp import TOTP

with open('../../config.json','r') as config_file:
    config = json.load(config_file)
TOTP("").now()
key_path = config['key_path']
key_secret_file = config['key_secret_file']
instrument_url = config['instrument_url']
output_file_path = config['output_file_path']
os.chdir(key_path)
key_secret = open(key_secret_file, "r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

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
    df_data.to_csv(output_file_path+str(today)+'.csv')

BN_hist_data("99926009","FIVE_MINUTE",st_date, end_date, instrument_list)


