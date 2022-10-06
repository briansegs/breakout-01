import ccxt
import json
import pandas as pd
import config as c
from datetime import date, datetime, timezone, tzinfo
import time, schedule

kucoin = ccxt.kucoinfutures({
    'enableRateLimit': True,
    'apiKey': c.kc_futures['API_KEY'],
    'secret': c.kc_futures['API_SECRET'],
    'password': c.kc_futures['API_PASSPHRASE'],
})

# Params:
symbol = 'XBTUSDTM'
pos_size = 100 # 125, 75,
params = {'timeInForce': 'PostOnly'}
target = 35
max_loss = -55
vol_decimal = .4

# For dataframe:
timeframe = '4h'
limit = 100
sma = 20

index_pos = 1

# Time between trades
pause_time = 60

# For volume calc
# vol_repeat * vol_time == TIME of volume collection
vol_repeat = 11
vol_time = 5





def ask_bid(symbol=symbol):
    '''
    Ask bid:
    ask_bid(symbol): if no argument, uses defaults
    Returns: ask, bid
    '''
    ob = kucoin.fetch_order_book(symbol)
    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    print(f'ask_bid: symbol: {symbol} | ask: {ask} | bid: {bid}')
    return ask, bid


# 6:16

def creat_dataframe(symbol, timeframe, limit):
    bars = kucoin.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    df_sma = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    return df_sma

def add_sma_to_dataframe(dataframe, sma, timeframe):
    bid = ask_bid(symbol)[1]
    title = f'sma{sma}_{timeframe}'

    dataframe[title] = dataframe.close.rolling(sma).mean()
    sma_value = dataframe[title]

    dataframe.loc[sma_value > bid, 'signal'] = 'SELL'
    dataframe.loc[sma_value < bid, 'signal'] = 'BUY'

    return dataframe

def df_sma(symbol=symbol, timeframe=timeframe, limit=limit, sma=sma):
    '''
    Creates a dataframe, appends sma and trade signal columns. Returns dataframe.
    df_sma(symbol, timeframe, limit, sma): if no argument, uses defaults
    Returns: df_sma
    '''
    print('Creating Dataframe...')
    dataframe = creat_dataframe(symbol, timeframe, limit)

    print('Adding SMA to Dataframe...')
    df_sma = add_sma_to_dataframe(dataframe, sma, timeframe)

    print('Returning Dataframe...')
    print(df_sma)
    return df_sma


# 25:00
# TODO: make a function that loops through dictionary and assigns index to symbol
def open_positions(symbol=symbol):
    '''
    Open positions:
    open_positions(symbol): if no argument, uses defaults
    Returns: open_positions, openpos_bool, openpos_size, long, index
    '''
    # what is the position index for that symbol?
    # 43:00

    if symbol == 'XBTUSDTM':
        index = 0
    elif symbol == 'SOLUSDTM':
        index = 1
    else:
        index = None

    open_positions = kucoin.fetch_positions()
    position_side = open_positions[index]['side']
    position_size = open_positions[index]['contractSize']

    if position_side == ('long'):
        openpos_bool = True
        long = True
    elif position_side == ('short'):
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None

    print(f'symbol: {symbol} | openpos_bool: {openpos_bool} | position size: {position_size} | long: {long}')
    return open_positions, openpos_bool, position_size, long, index

# 36:00
# Notes:
#   - kill_switch() needs open_positions() to work correctly
# kill_switch: pass in (symbol) if no symbol uses default
def kill_switch(symbol=symbol):
    print(f'starting the kill switch for {symbol}')
    openposi = open_positions(symbol)[1] # true or false
    long = open_positions(symbol)[3]# true or false
    kill_size = open_positions(symbol)[2]# size of open position

    print(f'openposi {openposi}, long {long}, size {kill_size}')

    while openposi == True:
        print('starting kill switch loop til limit fil..')
        temp_df = pd.DataFrame()
        print('just made a temp df')

        #kucoin.cancel_all_orders(symbol)
        openposi = open_positions(symbol)[1]
        long = open_positions(symbol)[3]# true or false
        kill_size = open_positions(symbol)[2]
        kill_size = int(kill_size)

        ask = ask_bid(symbol)[0]
        bid = ask_bid(symbol)[1]

        if long == False:
            #kucoin.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f'just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}')
            print(f'sleeping for 30 seconds to see of it fills..')
            time.sleep(30)
        elif long == True:
            #kucoin.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f'just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}')
            print('sleeping for 30 seconds to see of it fills..')
            time.sleep(30)
        else:
            print('++++++ SOMETHING I DIDNT EXPECT IN KILL SWITCH FUNCTION')

        openposi = open_positions(symbol)[1]

# 50:00
# sleep_on_close:
#   - pulls closed orders
#   - if last close was in last 59min then sleep for 1min
#   - sincelasttrade = minutes since last trade
#   - puase in mins
def sleep_on_close(symbol=symbol, pause_time=pause_time):
    closed_orders = kucoin.fetch_closed_orders(symbol)
    #print(closed_orders)

    for ord in closed_orders[-1::-1]:
        sincelasttrade = pause_time - 1 # how long we pause

        filled = False

        status = ord['info']['ordStatus']
        txttime = ord['info']['transactTimes']
        txttime = int(txttime)
        txttime = round((txttime/1000000000)) # bc in nanoseconds
        print(f'for {symbol} this is the status of the order {status} with epoch {txttime}')
        print('next iteration...')
        print('--------')

        if status == 'Filled':
            print('FOUND the order with last fill..')
            print(f'for {symbol} this is the time {txttime} this is the orderstatus {status}')
            orderbook = kucoin.fetch_order_book(symbol)
            ex_timestamp = orderbook['timestamp'] # in ms
            ex_timestamp = int(ex_timestamp/1000)
            print('---- below is the transaction time then exchange epoch time')
            print(txttime)
            print(ex_timestamp)

            time_spread = (ex_timestamp - txttime)/60

            if time_spread < sincelasttrade:
                #print('time since last trade is less than time spread')
                ##if in posis true, put a close order here
                #if in_pos == True:
                sleepy = round(sincelasttrade-time_spread)*60
                sleepy_min = sleepy/60

                print(f'the time spread is less than {sincelasttrade} mins its been {time_spread}mins.. so we SlEEP')
                time.sleep(60)

            else:
                print(f'its been {time_spread} mins since last fill so not sleeping cuz since last trade is {sincelasttrade}')
            break
        else:
            continue

    print(f'done with the sleep on close function for {symbol}..')

# 59:13
# orderbook:
def ob(symbol=symbol, vol_repeat=vol_repeat, vol_time=vol_time):
    print(f'fetching order book data for {symbol}...')

    df = pd.DataFrame()
    temp_df = pd.DataFrame()

    ob = kucoin.fetch_order_book(symbol)
    #print(ob)
    bids = ob['bids']
    asks = ob['asks']

    first_bid = bids[0]
    first_ask = asks[0]

    bid_vol_list = []
    ask_vol_list = []

    # If SELL vol > buy vol AND profit target hit, exit
    # get last 1min of volume.. and if sell > buy vol do x
# TODO:
#   - make range a variable
    for x in range(vol_repeat):

        for set in bids:
        #print(set)
            price = set[0]
            vol = set[1]
            bid_vol_list.append(vol)
            #print(price)
            #print(vol)

            #print(bid_vol_list)
            sum_bidvol = sum(bid_vol_list)
            #print(sum_bidvol)
            temp_df['bid_vol'] = [sum_bidvol]

        for set in asks:
            #print(set)
            price = set[0] # [40000, 344]
            vol = set[1]
            ask_vol_list.append(vol)
            #print(price)
            #print(vol)

            sum_askvol = sum(ask_vol_list)
            temp_df['ask_vol'] = [sum_askvol]

        #print(temp_df)
        time.sleep(vol_time) # change back to 5 later
        df = df.append(temp_df)
        print(df)
        print(' ')
        print('------')
        print(' ')
    print(f'done collecting volume data for bids and asks..')
    print('calculating the sums..')
    total_bidvol = df['bid_vol'].sum()
    total_askvol = df['ask_vol'].sum()

    seconds = vol_time * vol_repeat
    mins = round(seconds / 60, 2)
    print(f'last {mins}mins for {symbol} this is total Bid Vol: {total_bidvol} | ask_vol: {total_askvol}')

    if total_bidvol > total_askvol:
        control_dec = (total_askvol/total_bidvol)
        print(f'Bulls are in control: {control_dec}')
        # if bulls are in control, use regular target
        bullish = True
    else:
        control_dec = (total_bidvol / total_askvol)
        print(f'Bears are in control: {control_dec}...')
        bullish = False

        # open_positions() open_positions, openpos_bool, openpos_size, long

        open_posi = open_positions(symbol)
        openpos_tf = open_posi[1]
        long = open_posi[3]
        print(f'openpos_tf: {openpos_tf} || long: {long}')

        # if target is hit, check book vol
        # if bool vol is < .4.. stay in pos... sleep?
        # need to check to see if long or short

        if openpos_tf == True:
            if long == True:
                print('we are in a long position...')
                if control_dec < vol_decimal: # vol_decimal set to .4 at top
                    vol_under_dec = True
                    #print('going to sleep for a minute.. cuz under vol decimal')
                    #time.sleep(6) # change to 60
                else:
                    print('volume is not under dec so setting vol_under_dec to False')
                    vol_under_dec = False
            else:
                print('we are in a short position...')
                if control_dec < vol_decimal: # vol_decimal set to .4 at top
                    vol_under_dec = True
                    #print('going to sleep for a minute.. cuz under vol decimal')
                    #time.sleep(6) # change to 60
                else:
                    print('volume is under dec so setting vol_under_dec to False')
                    vol_under_dec = False
        else:
            print('we are not in position...')
            vol_under_dec = None
        # when vol_under_dec == False AND target hit, then exit
        print(vol_under_dec)

        return vol_under_dec


# For Testing:
# positions = kucoin.fetch_positions()
# index = open_positions(symbol)[4]
# position = positions[index]
# current_price = ask_bid(symbol)[1]
# print(index)

# 1:13:40
# pnl_close() [0] pnlclose and [1] in_pos [2]size [3]long TF
# Notes:
#   - Doesn't work with ccxt.kucoin
#   - Try ccxt.kucoinfutures
def pnl_close(symbol=symbol):
    print(f'checking to see if its time to exit for {symbol}...')

    positions = kucoin.fetch_positions()

    index = open_positions(symbol)[4]
    position = positions[index]
    side = position['side']
    size = position['contractSize']
    entry_price = float(position['entryPrice'])
    leverage = float(position['leverage'])

    current_price = ask_bid(symbol)[1]

    print(f'side: {side} | entry_price: {entry_price} | lev: {leverage}')
    # short or long

    if side == 'long':
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False

    try:
        perc = round(((diff/entry_price) * leverage), 10)
    except:
        perc = 0

    percent = 100 * perc
    print(f'for {symbol} this is our PNL percentage: {(percent)}%')

    pnlclose = False
    in_pos = False

    if percent > 0:
        in_pos = True
        print(f'for {symbol} we are in a winning position')
        if percent > target:
            print(':) :) we are in profit & hit target.. checking volume to see if we should close')
            pnlclose = True
            vol_under_dec = ob(symbol) # return TF
            if vol_under_dec == True:
                print(f'volume is under the decimal threshold we set of {vol_decimal}')
                time.sleep(30)
            else:
                print(f':) :) :) starting the kill switch because we hit our target')
                #kill_switch()
        else:
            print('we have not hit our target yet')
    elif percent < 0: # -10, -20
        in_pos = True

        if percent <= max_loss: # under -55, -56
            print(f'we need to exit now down {percent}... so starting the kill switch..')
            #kill_switch()
        else:
            print(f'we are in a losing position of {percent}.. but chillen cause max loss')
    else:
        print('we are not in position')

    if in_pos == True:
        #if breaks over .8% over 15m sma, then close pos (STOP LOSS)

        timeframe = '15m'
        df_f = df_sma(symbol, timeframe, 100, 20)
        print(df_f)
        #df_f['sma20_15'] # last value of this
        last_sma15 = df_f.iloc[-1][f'sma{sma}_{timeframe}']
        last_sma15 = int(last_sma15)
        # pull current bid
        curr_bid = ask_bid(symbol)[1]
        curr_bid = int(curr_bid)
        print(curr_bid)

        sl_val = last_sma15 * 1.008
        print(sl_val)

#Note: Turn kill_switch() on

        # 5/11 - remove the below and implementing a 55% stop loss
            # in the pnl section
        #if curr_bid > sl_val:
        #    print('current bid is above stop loss value.. starting kill switch..')
        #    kill_switch(symbol)
        #else:
        #    print('chillen in position..')
    else:
        print('we are not in position..')

    print(f'for {symbol} just finished checking PNL close..')

    return pnlclose, in_pos, size, long


# 1:29:14
