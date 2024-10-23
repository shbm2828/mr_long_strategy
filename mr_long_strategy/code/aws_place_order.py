import json
from SmartApi import SmartConnect
from pyotp import TOTP

TOTP("").now()

with open('C:\git\mr_long_strategy\mr_long_strategy\config.json', 'r') as config_file:
    config = json.load(config_file)


key_path = config['key_path']
key_secret_file = config['key_secret_file']
instrument_url = config['instrument_url']
output_file_path = config['output_file_path']

#os.chdir(key_path)
key_secret = open(key_secret_file, "r").read().split()
obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())


def place_robo_order(strike_symbol, token, buy_sell, entry_price, lot_num, low, instrument_list, exchange='NFO'):
    entry_price = obj.ltpData(exchange,strike_symbol, token)['data']['ltp']
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
        "quantity": lot_num        
        }
    response = obj.placeOrder(params)
    return response


#order_res = place_robo_order_demo(strike_symbol_CE, token_CE, "BUY", 135, 15, instrument_list)

#reponce=obj.rmsLimit()   
    
def lot_number(strike_symbol,token, exchange=config['exchange'], fund_in=config['capital_in']):
    ltp = obj.ltpData(exchange,strike_symbol, token)['data']['ltp']
    lot_num = int(fund_in/(ltp*25))
    return (lot_num, ltp)
    
    
#lot = lot_number("NIFTY24OCT2424800CE", "43891")        
#type(lot)
    
    



