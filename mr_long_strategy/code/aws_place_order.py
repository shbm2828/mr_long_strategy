
def place_robo_order(strike_symbol_CE, token_CE, buy_sell, entry_price, low, quantity, instrument_list, exchange='NFO'):
    params = {
        "variety": "ROBO",
        "tradingsymbol": strike_symbol_CE,
        "symboltoken": token_CE,
        "transactiontype": buy_sell,
        "exchange": exchange,
        "ordertype": "LIMIT",
        "producttype": "BO",
        "duration": "DAY",
        "price": entry_price,
        "stoploss": entry_price - low,         #in point
        "squareoff": entry_price + 2*(entry_price - low),           #in point
        "trailingstoploss": entry_price - low,         #in point
        "quantity": quantity        
        }
    response = obj.placeOrder(params)
    return response




#strike_symbol_CE = "BANKNIFTY16OCT2451500PE"
#token_CE = 43709


def place_robo_order_demo(strike_symbol_CE, token_CE, buy_sell, entry_price, quantity, instrument_list, exchange='NFO'):
    params = {
        "variety": "ROBO",
        "tradingsymbol": strike_symbol_CE,
        "symboltoken": token_CE,
        "transactiontype": buy_sell,
        "exchange": exchange,
        "ordertype": "LIMIT",
        "producttype": "BO",
        "duration": "DAY",
        "price": entry_price,
        "stoploss": 30,         #in point
        "squareoff": 60,           #in point
        "trailingstoploss": 10,         #in point
        "quantity": quantity        
        }
    response = obj.placeOrder(params)
    return response
#order_res = place_robo_order_demo(strike_symbol_CE, token_CE, "BUY", 135, 15, instrument_list)

#placed_order_id = order_res['data']['orderid']





