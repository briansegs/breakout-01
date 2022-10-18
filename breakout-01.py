'''
calc the last 3 days of data
15m * 3day
96 15m periods in 1d, we want 3 day so 96 * 3 = 288 + 1 = 289
find the resistance and support  on 15min
on retest place orders
'XBTUSDTM'
1:41:55
'''
# TODO: lets import just the functions we need
import ccxt
# TODO: lets import just the functions we need
import pandas as pd
import config as c
import time, schedule
# TODO: lets import just the functions we need
import functions as f

kucoin = ccxt.kucoinfutures({
    'enableRateLimit': True,
    'apiKey': c.kc_futures['API_KEY'],
    'secret': c.kc_futures['API_SECRET'],
    'password': c.kc_futures['API_PASSPHRASE'],
})
# TODO: what params do i really need here?
# TODO: how should I work out passing arguments? when to use defaults?
# Params:
symbol = 'XBTUSDTM'

pos_size = 10 # 125, 75,
target = 9 # % gain I want
max_loss = -8

params = {'timeInForce': 'PostOnly'}

timeframe = '15m'
limit = 289
sma = 20

# 1:59:44
# TODO: make get functions for support and resistance
df_sma = f.df_sma(symbol, '15m', 289, 20) # 2d == 193, 3d == 289

curr_support = df_sma['close'].min()
curr_resis = df_sma['close'].max()
print(f'support {curr_support} | resis {curr_resis}')

# TODO: I think this can be better (rework)
# TODO: see if we can get these into one function
# TODO: lets see if we can move this to the functions.py file
def create_dataframe(symbol, timeframe, limit):
    '''
    Supports: df_wolast()
    '''
    data = kucoin.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    # Grabbing all but last bars
    df_sma_wolast = pd.DataFrame(data[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_sma_wolast['timestamp'] = pd.to_datetime(df_sma_wolast['timestamp'], unit='ms')

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

    return df_wolast

# TODO: pull in sleep on close
# sleep_on_close = f.sleep_on_close(symbol, pause_time)

# TODO: pull in kill switch
# kill_switch = f.kill_switch(symbol)

# 2:24:00

def retest():
    # TODO: do i need this print statment?
    print('creating retest number...')
    '''
    if support breaks - SHORT, place asks right below (.1% == .001)
    if resistance breaks - LONG, place bids right above (.1% == .001)
    '''
    buy_break_out = False
    sell_break_down = False
    # TODO: does it make more sense to init "breakoutprice" & "breakdownprice" with 0 instead of False?
    breakoutprice = False
    breakdownprice = False
    # TODO: is there a better way to name this?
    df_sma_wolast = df_wolast(symbol)
    bid = f.get_bid(symbol)

    # 3:28:39

    if bid > df_sma_wolast['resistance'].iloc[-1]:
        # TODO: do i need this statment? if so make this print statment more meaningful
        print(f'we are breaking out upwards... buy at previous resistance {curr_resis}')
        buy_break_out = True
        breakoutprice = int(df_sma_wolast['resistance'].iloc[-1]) * 1.001

    elif bid < df_sma_wolast['support'].iloc[-1]:
        # TODO: do i need this statment? if so make this print statment more meaningful
        print(f'we are breaking down... buy at previous support {curr_support}')
        sell_break_down = True
        breakdownprice = int(df_sma_wolast['support'].iloc[-1]) * .999

    return buy_break_out, sell_break_down, breakoutprice, breakdownprice

def bot():
    # TODO: I want to look at reducing the print statments. They are too messy to understand easily
    # TODO: I want to keep all the print statments or as many as make sense in this function
    f.pnl_close()
    position_data = f.position_data(symbol)
    bid = f.get_bid(symbol)
    # TODO: this is just being used for print statments
    buy_break_out, sell_break_down, breakoutprice, breakdownprice = retest()
    # TODO: do I need this print statment?
    print(f'breakout: {buy_break_out} {round(breakoutprice, 2)} | breakdown: {sell_break_down} {round(breakdownprice, 2)}')

    in_pos = position_data[1]
    # TODO: can I put int on position_data[2] instead?
    curr_size = position_data[2]
    curr_size = int(curr_size)
    # TODO: this is redundant. assign curr_p(current price) above to bid = f.get_bid(symbol)
    curr_p = bid
    # TODO: do I need this print statment
    print(f'symbol: {symbol} | buy_break_out: {buy_break_out} | sell_break_down: {sell_break_down} | inpos: {in_pos} | price: {curr_p}')

    # TODO: do I need () below? look into it
    # TODO: I don't think that position size will for for me using Kucoin. Figure out a better way of doing this
    if (in_pos == False) and (curr_size < pos_size):
        # kucoin.cancel_all_orders(symbol)
        print('kucoin.cancel_all_orders(symbol)')
        # TODO: can or should I use the calls above instead of calling them again in this if statment
        breakoutprice = retest[2]
        breakdownprice = retest[3]
        # TODO: why do we use buy_break_out from out of this if statment and say "breakoutprice" from inside the if statment?
        if buy_break_out == True:
            # TODO: can we clean up these print statments so they feel more meaningful?
            print('making an opening order as a BUY')
            print(f'{symbol} buy order of {pos_size} submitted @ {breakoutprice}')
            # kucoin.create_limit_buy_order(symbol, pos_size, breakoutprice, params)
            print('order submitted so sleep for 2mins...')
            time.sleep(120)
        elif sell_break_down == True:
            # TODO: can we clean up these print statments so they feel more meaningful?
            print('making an opening order as a SELL')
            print(f'{symbol} sell order of {pos_size} submitted @ {breakdownprice}')
            # kucoin.create_limit_sell_order(symbol, pos_size, breakdownprice, params)
            print('order submitted so sleep for 2mins...')
            time.sleep(120)
        else:
            print('not submitting any orders.. sleeping 1min')
            time.sleep(60)
    else:
        print('we are in position already so not making any orders')


schedule.every(28).seconds.do(bot)

while True:
    try:
        schedule.run_pending()
    except:
        print('***maybe an internet problem, code failed... sleep 30...')
        time.sleep(30)