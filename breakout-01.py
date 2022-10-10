# calc the last 3 days of data
# find the resistance and support  on 15min
# on retest place orders
# 'XBTUSDTM'
# 1:41:55

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
df_sma = f.df_sma(symbol, '15m', 200, 20)

# TODO: pull in open positions
open_pos = f.position_data(symbol)

# TODO: Add support/resist to functions
# TODO: Pull in data:
# TODO: Calculate support & resistance based on close
# TODO: Calculate retest where we put orders

# TODO: pull in pnl close - 2:04:31
pnl_close = f.pnl_close(symbol)

# TODO: pull in sleep on close
sleep_on_close = f.sleep_on_close(symbol, pause_time)

# TODO: pull in kill switch
kill_switch = f.kill_switch(symbol)

# TODO: Run bot
def bot():
    print('starting bot... ')

# TODO: scheduling the bot
# schedule.every(28).seconds.do(bot)

# while True:
#     try:
#         schedule.run_pending()
#     except:
#         print('***maybe an internet problem, code failed... sleep 30...')
#         time.sleep(30)