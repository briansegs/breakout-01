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
timeframe = '15m'
limit = 289
sma = 20

index_pos = 1

# Time between trades
pause_time = 60

# For volume calc
# vol_repeat * vol_time == TIME of volume collection
vol_repeat = 5
vol_time = 5


# Support functions:
def create_dataframe(symbol, timeframe, limit):
    '''
    Supports: df_sma()
    '''
    data = kucoin.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    df_sma = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma['timestamp'] = pd.to_datetime(df_sma['timestamp'], unit='ms')

    return df_sma

def add_sma_to_dataframe(dataframe, sma, timeframe):
    '''
    Supports: df_sma()
    '''
    bid = ask_bid(symbol)[1]
    title = f'sma{sma}_{timeframe}'

    dataframe[title] = dataframe.close.rolling(sma).mean()
    sma_value = dataframe[title]

    dataframe.loc[sma_value > bid, 'signal'] = 'SELL'
    dataframe.loc[sma_value < bid, 'signal'] = 'BUY'

    add_support_resistance(dataframe)

    return dataframe

def add_support_resistance(dataframe):
    '''
    Supports: add_sma_to_dataframe()
    '''
    dataframe['support'] = dataframe['close'].min()
    dataframe['resistance'] = dataframe['close'].max()
    return dataframe

def get_index(symbol):
    '''
    Supports: position_data() was open_positions()
    '''
    if symbol == 'XBTUSDTM':
        index = 0
    elif symbol == 'SOLUSDTM':
        index = 1
    else:
        index = None
    return index

def get_open_long(position_side):
    '''
    Supports: position_data() was open_positions()
    '''
    if position_side == ('long'):
        is_open = True
        is_long = True
    elif position_side == ('short'):
        is_open = True
        is_long = False
    else:
        is_open = False
        is_long = None
    return is_open, is_long

def close_short(symbol, kill_size, bid, params):
    '''
    Supports: kill_switch()
    '''
    #kucoin.create_limit_buy_order(symbol, kill_size, bid, params)
    print(f'just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}')
    print(f'sleeping for 30 seconds to see of it fills..')

def close_long(symbol, kill_size, ask, params):
    '''
    Supports: kill_switch()
    '''
    #kucoin.create_limit_sell_order(symbol, kill_size, ask, params)
    print(f'just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}')
    print('sleeping for 30 seconds to see of it fills..')

def get_orderbook_asks_bids(symbol):
    '''
    Supports: ob()
    '''
    ob = kucoin.fetch_order_book(symbol)
    bids = ob['bids']
    asks = ob['asks']
    first_bid = bids[0]
    first_ask = asks[0]
    return asks, bids

def calc_sums(df, vol_time, vol_repeat):
    '''
    Supports: ob()
    '''
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
    return control_dec, bullish

def get_ob_open_long(symbol):
    '''
    Supports: ob()
    '''
    position = position_data(symbol)
    is_open = position[1]
    is_long = position[3]
    print(f'{symbol} open: {is_open} || long: {is_long}')
    return is_open, is_long

def is_vol_under_dec(is_long, is_open, control_dec, vol_decimal):
    '''
    Supports: ob()
    '''
    if is_open == True:
        if is_long == True:
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
    return vol_under_dec

def get_pnl_percent(symbol):
    '''
    Supports pnl_close()
    '''
    positions = kucoin.fetch_positions()
    index = position_data(symbol)[4]
    position = positions[index]
    realized_pnl = position['info']['realisedPnl']

    df = pd.DataFrame(position, columns = [
        'symbol',
        'side',
        'entryPrice',
        'liquidationPrice',
        'markPrice',
        'collateral',
        'realisedPnl',
        'unrealizedPnl',
        'percentage',
        'leverage',
        'contractSize'
        ], index=[0])

    size = df['contractSize'][0]
    side = df['side'][0]
    pnl_percent = df['percentage'][0] * 100

    df['collateral'] =  round(df['collateral'], 2)
    df['realisedPnl'] = realized_pnl
    df['percentage'] = "{:.2%}".format(df['percentage'][0])

    if side == 'long':
        long = True
    else:
        long = False

    print(df)

    return pnl_percent, long, size

def profit_flow(pnl_percent, target, symbol, pnlclose):
    '''
    Supports pnl_close()
    '''
    in_pos = True
    print(f'for {symbol} we are in a winning position')
    if pnl_percent > target:
        print(':) :) we are in profit & hit target.. checking volume to see if we should close')
        pnlclose = True
        vol_under_dec = ob(symbol) # returns T/F
        if vol_under_dec == True:
            print(f'volume is under the decimal threshold we set of {vol_decimal}')
            time.sleep(30)
        else:
            print(f':) :) :) starting the kill switch because we hit our target')
            #kill_switch()
    else:
        print('we have not hit our target yet')
    return in_pos, pnlclose

def loss_flow(pnl_percent):
    '''
    Supports pnl_close()
    '''
    in_pos = True

    if pnl_percent <= max_loss: # under -55, -56
        print(f'we need to exit now! down {pnl_percent}... so starting the kill switch..')
        #kill_switch()
    else:
        print(f'we are in a losing position of {pnl_percent}.. but chillen cause max loss')
    return in_pos

def buy_sell_flow(pnl_percent):
    '''
    Supports pnl_close()
    '''
    pnlclose = False
    in_pos = False

    if pnl_percent > 0:
        in_pos, pnlclose = profit_flow(pnl_percent, target, symbol, pnlclose)
    elif pnl_percent < 0:
        in_pos = loss_flow(pnl_percent)
    else:
        print('we are not in position')

    if in_pos == True:
        #if breaks over .8% over 15m sma, then close pos (STOP LOSS)

        timeframe = '15m'
        df_f = df_sma(symbol, timeframe, 100, 20)
        #df_f['sma20_15'] # last value of this
        last_sma15 = df_f.iloc[-1][f'sma{sma}_{timeframe}']
        last_sma15 = int(last_sma15)
        # pull current bid
        curr_bid = ask_bid(symbol)[1]
        curr_bid = int(curr_bid)
        print(f'curr_bid: {curr_bid}')

        sl_val = last_sma15 * 1.008
        print(f'sl_val: {sl_val}')

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

    return pnlclose, in_pos


# 6:16
def ask_bid(symbol=symbol):
    '''
    Ask bid:
    ask_bid(symbol): if no argument, uses defaults
    Returns: ask, bid
    '''
    ob = kucoin.fetch_order_book(symbol)
    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    return ask, bid

def get_ask(symbol=symbol):
    '''
    ask_bid(symbol): if no argument, uses defaults
    Returns: ask
    '''
    orderbook = kucoin.fetch_order_book(symbol)
    ask = orderbook['asks'][0][0]
    return ask

def get_bid(symbol=symbol):
    '''
    ask_bid(symbol): if no argument, uses defaults
    Returns: ask
    '''
    orderbook = kucoin.fetch_order_book(symbol)
    bid = orderbook['bids'][0][0]
    return bid

# 25:00
def df_sma(symbol=symbol, timeframe=timeframe, limit=limit, sma=sma):
    '''
    Creates a dataframe, appends sma and trade signal columns. Returns dataframe.
    df_sma(symbol, timeframe, limit, sma): if no argument, uses defaults
    Returns: df_sma
    '''
    print('Creating Dataframe...')
    dataframe = create_dataframe(symbol, timeframe, limit)

    print('Adding SMA to Dataframe...')
    df_sma = add_sma_to_dataframe(dataframe, sma, timeframe)

    print('Returning Dataframe...')
    print(df_sma)
    return df_sma

# TODO: make a function that loops through dictionary and assigns index to symbol
# 43:00
def position_data(symbol=symbol):
    '''
    Pulls, prints, and returns data for selected symbol.
    position_data(symbol): if no argument, uses defaults
    Returns: open_positions, is_open, position_size, is_long, index
    '''
    open_positions = kucoin.fetch_positions()
    index = get_index(symbol)
    position = open_positions[index]

    position_side = position['side']
    position_size = position['contractSize']
    is_open, is_long = get_open_long(position_side)

    print(f'symbol: {symbol} | is_open: {is_open} | position size: {position_size} | is_long: {is_long}')
    return open_positions, is_open, position_size, is_long, index

# 36:00
# Notes:
#   might need to play around with kill size to get limit orders to work
def kill_switch(symbol=symbol):
    '''
    Runs a loop that cancels all orders and creates a
    limit buy (if short) or sell (if long) order to take
    you out of selected open position.
    kill_switch(symbol): if no argument, uses defaults
    '''
    print(f'starting the kill switch for {symbol}:')
    is_open = position_data(symbol)[1]
    is_long = position_data(symbol)[3]
    kill_size = position_data(symbol)[2]# size of open position
    print(f'is_open: {is_open} | is_long: {is_long} | size: {kill_size}')

    while is_open == True:
        print('starting kill switch loop till limit fill..')
        print('cancelling all orders...')
        #kucoin.cancel_all_orders(symbol)

        is_open = position_data(symbol)[1]
        is_long = position_data(symbol)[3]
        kill_size = position_data(symbol)[2]
        kill_size = int(kill_size)
        ask, bid = ask_bid(symbol)

        if is_long == False:
            close_short(symbol, kill_size, bid, params)
            time.sleep(30)
        elif is_long == True:
            close_long(symbol, kill_size, ask, params)
            time.sleep(30)
        else:
            print('++++++ SOMETHING I DIDNT EXPECT IN KILL SWITCH FUNCTION')

        is_open = position_data(symbol)[1]

# Testing: sleep on close
# closed_orders = kucoin.fetch_closed_orders(symbol)
# xtx = closed_orders[0]['info']['orderTime']
# xtx = int(xtx)
# xtx = round((xtx/1000000000))
# print(xtx)

# 50:00
# sleep_on_close:
#   - needs more work...
#   - pulls closed orders
#   - if last close was in last 59min then sleep for 1min
#   - sincelasttrade = minutes since last trade
#   - puase in mins
def sleep_on_close(symbol=symbol, pause_time=pause_time):
    '''
    Pulls closed orders.
    If last close was in last 59min then sleep for 1min.
    sleep_on_close(symbol, pause_time): if no argument, uses defaults
    '''
    closed_orders = kucoin.fetch_closed_orders(symbol)
    #print(closed_orders)

    for ord in closed_orders[-1::-1]:
        sincelasttrade = pause_time - 1 # how long we pause in min

        filled = False

        status = ord['info']['status']
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
    '''
    If sell vol > buy vol and profit target hit, exit.
    Gets last 1min of volume.. and if sell > buy vol do x
    ob(symbol, vol_repeat, vol_time): if no argument, uses defaults
    Returns: vol_under_dec(bool)
    '''
    print(f'fetching order book data for {symbol}...')

    df = pd.DataFrame()
    temp_df = pd.DataFrame()
    asks, bids =  get_orderbook_asks_bids(symbol)
    bid_vol_list = []
    ask_vol_list = []

    for x in range(vol_repeat):
        for set in bids:
            price = set[0]
            vol = set[1]
            bid_vol_list.append(vol)
            sum_bidvol = sum(bid_vol_list)
            temp_df['bid_vol'] = [sum_bidvol]

        for set in asks:
            price = set[0] # [40000, 344]
            vol = set[1]
            ask_vol_list.append(vol)
            sum_askvol = sum(ask_vol_list)
            temp_df['ask_vol'] = [sum_askvol]

        time.sleep(vol_time) # change back to 5 later
        df = df.append(temp_df)
        print(df)
        print(' ')
        print('------')
        print(' ')
    print(f'done collecting volume data for bids and asks..')
    print('calculating the sums..')

    # if target is hit, check book vol
    # if bool vol is < .4.. stay in pos... sleep?
    # need to check to see if long or short

    control_dec, bullish = calc_sums(df, vol_time, vol_repeat)
    is_open, is_long = get_ob_open_long(symbol)
    vol_under_dec = is_vol_under_dec(is_long, is_open, control_dec, vol_decimal)

    # when vol_under_dec == False AND target hit, then exit
    print(f'vol_inder_dec: {vol_under_dec}')

    return vol_under_dec

# 1:13:40
# Notes:
#   - Still needs work...
def pnl_close(symbol=symbol):
    '''
    Gets the pnl percent of selected symbol.
    Buys or sells based on pnl percent logic.
    pnl_close(symbol): if no argument, uses defaults
    Returns: pnlclose, in_pos, size, long
    '''
    print(f'checking to see if its time to exit for {symbol}...')

    pnl_percent, long, size = get_pnl_percent(symbol)

    pnlclose, in_pos = buy_sell_flow(pnl_percent)

    print(f'for {symbol} just finished checking PNL close..')

    return pnlclose, in_pos, size, long


# 1:29:14
