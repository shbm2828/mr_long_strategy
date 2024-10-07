import datetime

def get_nearest_exp():
    today = datetime.date.today()
    # Calculate the number of days until the next Wednesday
    days_until_next_wednesday = (2 - today.weekday()) % 7

    # Add the days to today's date to get the next Wednesday
    next_wednesday = today + datetime.timedelta(days=days_until_next_wednesday)
    nearest_exp = next_wednesday.strftime("%d%b%y")
    return nearest_exp

expiry=get_nearest_exp()
strike_price = 51300
print(type(expiry))

strike_symbol = 'BANKNIFTY'+expiry+str(strike_price)+'CE'
print(strike_symbol)
#BANKNIFTY09OCT2449300CE
