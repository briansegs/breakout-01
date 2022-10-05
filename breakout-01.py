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

symbol = 'XBTUSDTM'
