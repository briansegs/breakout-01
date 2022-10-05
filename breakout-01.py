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

# Time between trades
pause_time = 10

# For volume calc
# vol_repeat * vol_time == TIME of volume collection
vol_repeat = 11
vol_time = 5

pos_size = 10 # 125, 75,
params = {'timeInForce': 'PostOnly'}
target = 9
max_loss = -8
vol_decimal = .4


# TODO: Add support/resist to functions
# TODO: Pull in data: 1:50:21
# TODO: Calculate support & resistance based on close
# TODO: Calculate retest where we put orders
# TODO: Run bot




