'''
calc the last 3 days of data
15m * 3day
96 15m periods in 1d, we want 3 day so 96 * 3 = 288 + 1 = 289
find the resistance and support  on 15min
on retest place orders
'XBTUSDTM'
1:41:55
'''

import ccxt
import json
import pandas as pd
import config as c
from datetime import date, datetime, timezone, tzinfo
import time, schedule
import functions as f

kucoin = ccxt.kucoinfutures({
    'enableRateLimit': True,
    'apiKey': c.kc_futures['API_KEY'],
    'secret': c.kc_futures['API_SECRET'],
    'password': c.kc_futures['API_PASSPHRASE'],
})

# Params:
symbol = 'XBTUSDTM'
index_pos = 0 # Change based on what asset

pos_size = 10 # 125, 75,
target = 9 # % gain I want
max_loss = -8

# Time between trades
pause_time = 10

# For volume calc
# vol_repeat * vol_time == TIME of volume collection
vol_repeat = 11
vol_time = 5


params = {'timeInForce': 'PostOnly'}
vol_decimal = .4

# 1:50:21

# TODO: pull in ask and bid
ask, bid = f.ask_bid()
print(f'For {symbol}... ask: {ask} | bid: {bid}')

# TODO: pull in df sma - has all the data we need - 1:59:44
df_sma = f.df_sma(symbol, '15m', 289, 20) # 2d == 193, 3d == 289


timeframe = '15m'
limit = 289
sma = 20

def create_dataframe(symbol, timeframe, limit):
    '''
    Supports: df_wolast()
    '''
    data = kucoin.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    # Grabbing all but last bars
    df_sma_wolast = pd.DataFrame(data[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma_wolast['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    return df_sma_wolast

def df_wolast(symbol=symbol, timeframe=timeframe, limit=limit, sma=sma):
    '''
    Creates a dataframe, appends sma and trade signal columns. Returns dataframe.
    df_sma(symbol, timeframe, limit, sma): if no argument, uses defaults
    Returns: df_sma
    '''
    print('Creating Dataframe...')
    dataframe = create_dataframe(symbol, timeframe, limit)

    print('Adding SMA to Dataframe...')
    df_wolast = f.add_sma_to_dataframe(dataframe, sma, timeframe)

    print('Returning Dataframe (df_wolast)...')
    print(df_wolast)
    return df_wolast

# TODO: pull in open positions
open_pos = f.position_data(symbol)

# TODO: Add support/resist to functions
# TODO: Pull in data:

# TODO: Calculate support & resistance based on close
curr_support = df_sma['close'].min()
curr_resis = df_sma['close'].max()
print(f'support {curr_support} | resis {curr_resis}')

# TODO: pull in pnl close - 2:04:31
# pnl_close = f.pnl_close(symbol)

# TODO: pull in sleep on close
# sleep_on_close = f.sleep_on_close(symbol, pause_time)


# TODO: pull in kill switch
# kill_switch = f.kill_switch(symbol)

# TODO: Run bot
# TODO: Calculate retest where we put orders 2:24:00

def retest():
    print('creating retest number...')
    '''
    if support breaks - SHORT, place asks right below (.1% == .001)
    if resistance breaks - LONG, place bids right above (.1% == .001)
    '''
    buy_break_out = False
    sell_break_down = False
    breakoutprice = False
    breakdownprice = False

    df_sma_wolast = df_wolast(symbol)
    # maybe we want to do this on the bid...
    # if most current df resistance <= df_wolast:

    # 3:28:39

    if bid > df_sma['resistance'].iloc[-1]:
        print(f'we are breaking out upwards... buy at previous resistance {curr_resis}')
        # input buy logic
        buy_break_out = True
        breakoutprice = int(df_sma['resistance'].iloc[-1]) * 1.001
    elif bid < df_sma['support'].iloc[-1]:
        print(f'we are breaking down... buy at previous support {curr_support}')
        # input sell logic
        sell_break_down = True
        breakdownprice = int(df_sma['support'].iloc[-1]) * .999

    return buy_break_out, sell_break_down, breakoutprice, breakdownprice



def bot():

    f.pnl_close()

    ask, bid = f.ask_bid()

    buy_break_out, sell_break_down, breakoutprice, breakdownprice = retest()
    print(f'breakout: {buy_break_out} {round(breakoutprice, 2)} | breakdown: {sell_break_down} {round(breakdownprice, 2)}')

    time.sleep(3344)

    in_pos = open_pos[1]
    curr_size = open_pos[2]
    curr_size = int(curr_size)

    curr_p = bid

    print(f'symbol: {symbol} | buy_break_out: {buy_break_out} | sell_break_down: {sell_break_down} | inpos: {in_pos} | price: {curr_p}')

    if (in_pos == False) and (curr_size < pos_size):
        # kucoin.cancel_all_orders(symbol)
        print('kucoin.cancel_all_orders(symbol)')
        ask, bid = f.ask_bid()

        if buy_break_out == True:
            print('making an opening order as a BUY')
        elif sell_break_down == True:
            print('making an opening order as a SELL')
        else:
            print('not submitting any orders.. sleeping 1min')
            time.sleep(60)
    else:
        print('we are in position already so not making any orders')

bot()

# TODO: scheduling the bot
# schedule.every(28).seconds.do(bot)

# while True:
#     try:
#         schedule.run_pending()
#     except:
#         print('***maybe an internet problem, code failed... sleep 30...')
#         time.sleep(30)