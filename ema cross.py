import pandas as pd
pd.set_option('display.max_rows',None)
import ccxt
import ta
from ta.trend import EMAIndicator
import schedule
import time
import logging

#输出日志文件
logging.basicConfig(level=logging.INFO,#控制台打印的日志级别
                    filename='new.log',
                    filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    #a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s %(message)s'
                    #日志格式
                    )

direction  = 1 # 初始方向为向上（ema33 在 ema55 之上）
id = 'F41346A89A474C2CB4EC865C85400F22'
key = '99718AAF9BE641AAB1BA58C1BC0BC7170FECD008BC208616'

exchange = ccxt.coinex(
    {
        'apiKey':id,
        'secret':key
    }
)

#每半小时，读取一次蜡烛图，看看有没有金叉或者死叉
def get_info(period = '30m'):
    bars = exchange.fetch_ohlcv('CET/USDT', timeframe= period)
    df = pd.DataFrame(bars, columns= ['timestamp', 'open', 'high', 'low', 'close', 'volumn'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit= 'ms')
    df['ema33'] = EMAIndicator(df['close'], window= 33).ema_indicator()
    df['ema55'] = EMAIndicator(df['close'], window= 55).ema_indicator()
    return df

#初始化
#先判断初始方向：
#33在55之上，牛市
#33在55之下，熊市
#33上穿55，金叉
#33下穿55，死叉
def init():
    global direction
    df = get_info()
    pos = len(df.index)-1
    if(df['ema55'][pos] - df['ema33'][pos]) >= 0:
        direction = 0 # 熊市
    else:
        direction = 1

def cross_check(df):
    global direction
    pos = len(df.index) - 1
    diff = df['ema33'][pos] - df['ema55'][pos]
    if (diff >= 0) and (direction == 1):
        logging.info("ema33 %f,  ema55 %f 牛市继续,满仓(现有仓位保持不动)" % (df['ema33'][pos], df['ema55'][pos]))
        print('牛市继续,满仓(现有仓位保持不动')
    elif (diff < 0 and direction == 1):
        logging.info("ema33 %f,  ema55 %f 死叉,卖出所有仓位" % (df['ema33'][pos] ,df['ema55'][pos]))
        get_balance_and_sell()
        direction = 0
        print('死叉,卖出所有仓位')
    elif (diff >= 0) and (direction == 0):
        logging.info("ema33 %f,  ema55 %f 金叉,买入所有仓位" % (df['ema33'][pos], df['ema55'][pos]))
        direction = 1
        get_balance_and_buy()
        print('金叉,买入所有仓位')
    elif (diff < 0 and direction == 0):
        logging.info("ema33 %f,  ema55 %f 熊市继续,空仓(现有仓位保持不动)" % (df['ema33'][pos] ,df['ema55'][pos]))
        print('熊市继续,空仓(现有仓位保持不动')
def get_balance_and_sell():
    balances = exchange.fetch_balance()
    coin_amount = balances['total']['CET']
    #把coin 全卖了
    if coin_amount > 10:
        exchange.create_market_sell_order('CET/USDT',coin_amount)

def get_balance_and_buy():
    balances = exchange.fetch_balance()
    usdt_amount = balances['total']['USDT']
    #把usdt 全买了coin
    exchange.options['createMarketBuyOrderRequiresPrice'] = False
    if usdt_amount > 2:
        exchange.create_market_buy_order('CET/USDT', usdt_amount)

def run():
    df = get_info('1m')
    cross_check(df)

if __name__ == '__main__':
    init()
    schedule.every(1).minutes.do(run)
    while True:
        schedule.run_pending()
        time.sleep(1)

