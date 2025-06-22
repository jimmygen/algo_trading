import pandas as pd
import os
import quantindicators as qi
from dotenv import load_dotenv
from backtesting import Backtest, Strategy

## Fetch data ##

broker = 'binance'
symbol = 'BTC/USD' # Or 'BTC/USD', 'ETH/USDT', etc. Check Deribit's symbol format.
interval = "1h" #1m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 1W 1M
lookback_days = 50 # Your desired lookback
custom_daily_candle_close_hour = 22 # 10 PM CEST

file_location = "F:\TradingBot\data\hour\BTCUSDT_1h_2015-01-01_to_2025-06-01.csv"
df_raw = pd.read_csv(file_location)

target_fixed_cet = 'Etc/GMT-1'
#print(df_raw.tail())
#df_raw['time'] = df_raw['time'].tz_convert(target_fixed_cet)
df_raw['time'] = pd.to_datetime(df_raw['time'], format="%Y-%m-%dT%H:%M:%SZ")
df_raw = df_raw.set_index('time')
df_raw.index.name = 'timestamp'
df_raw.index = df_raw.index.tz_localize('UTC')

df_raw_cet = df_raw.copy()
df_raw_cet.index = df_raw_cet.index.tz_convert('Europe/Amsterdam')

print(df_raw.tail())
print(df_raw_cet.tail())
# Ensure the DataFrame timezone is consistent for resampling
#local_tz = pytz.timezone('Europe/Amsterdam')
#df_raw = df_raw.tz_convert(local_tz)


print(f"Raw hourly data fetched: {len(df_raw)} candles from {df_raw.index.min()} to {df_raw.index.max()}")

offset_hours = custom_daily_candle_close_hour - 24 # 22 - 24 = -2 hours
offset_str = f'{offset_hours}h' # This creates a string like '-2H'

# Resample to custom daily candles (24h) starting/closing at 10 PM CEST
df = df_raw_cet.resample('24h', origin='start_day', offset=offset_str, label='right', closed='right').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})

df = df.dropna()
df = df.iloc[:-1] #Remove last day
df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})

print(f"\nResampled to custom daily candles (closed 10 PM CEST):")
print(f"Number of daily candles: {len(df)}")
print(f"First daily candle: {df.index.min()} (close time)")
print(f"Last daily candle: {df.index.max()} (close time)")
print("\nLast 5 custom daily candles:")
print(df.tail())


class MomentumStrategy(Strategy):
    #optimization variables
    thr_pr_enter = 0.8
    thr_vol_enter = 0.5
    thr_pr_exit = 0.7

    def init(self):
        #print(f"input data is {self.data.Close}")
        self.sma = self.I(qi.MovingAverage, self.data.Close, 20, 'sma', overlay=True, name="SMA_20")
        self.ema = self.I(qi.MovingAverage, self.data.Close, 20, 'ema', overlay=True, name="EMA_20")
        self.wma = self.I(qi.MovingAverage, self.data.Close, 20, 'wma', overlay=True, name="WMA_20")
        self.atr = self.I(qi.AverageTrueRange, self.data, 14, overlay=False, name="ATR_14")
        self.vol = self.I(qi.MovingAverage, self.data.Volume, 20, 'ema', name="Volume")
        self.dfdt = self.I(qi.Derivative, self.data.Close, name="DfDt")
        self.commission=0.0025
        self.entry1 = self.I(qi.MomentumSignalEntry, self.data, 20, name="MomentumSignalEntry")
        self.entry2 = self.I(qi.VolumeSignalEntry, self.data.Volume, 20, name="VolumeSignalEntry")
        self.exit1 = self.I(qi.MomentumSignalExit, self.data, 20, name="MomentumExitSignal")
        #df['entry_signal_2'] = df['Volume']-df['vol_ema']*1.5
        #df['exit_signal_1'] = df['ema']+df['atr']*0.5-df['Close']
        #self.cls = self.I(self.data.Close, "name=Close")
        #self.dtdtt = self.I(Derivative, self.dfdt, name="DfDtt")
           
    def next(self):
        price = self.data.Close[-1]
        ema = self.ema[-1]
        time = self.data.index[-1]
        atr = self.atr[-1]
        vol = self.vol[-1]
        #if price >= ema*1.02 and self.position.size == 0:
        if self.position.size == 0:
            if price >= ema+atr*1.5*self.thr_pr_enter and self.data.Volume[-1] > vol*1.5*self.thr_vol_enter:
                print(f"Currently holding {self.position.size} positions")
                print(f"cash is {self.equity}")
                n_buy = int(self.equity*0.99//(price*(1+self.commission)))      
                trade = self.buy(size=n_buy, limit=None)
                #trade = self.buy(size=1, limit=None)
                print(f"{time}: \n{n_buy} {symbol} positions bought at {price}")  
                print(f"Total cost of {price*n_buy*(1+self.commission)} \n")
                self.highest = price

        else:
            if price <= ema+atr*1.5*self.thr_pr_exit:
                print(self.position.size)
                self.position.close()
                profit = self.position.pl
                print(f"{time}: {symbol} sold at {price}")
                print(f"profit is {profit} \n")
            #print(f"Current price is {price}")
            #if price > self.highest:
            #    self.highest = price
            #    print(f"New high is {self.highest}")
            #if price <= self.highest*0.9:
            #    print(self.position.size)
            #    self.position.close()
            #    profit = self.position.pl
            #    print(f"{time}: {symbol} sold at {price} Reason: Trailing Stop Loss")
            #    print(f"profit is {profit} \n")
class SmoothDerivStrategy(Strategy):
    def init(self):
        print(f"input data is {self.data.Close}")
        self.sma = self.I(qi.MovingAverage, self.data.Close, 20, 'sma', overlay=True, name="SMA_20")
        self.ema = self.I(qi.MovingAverage, self.data.Close, 20, 'ema', overlay=True, name="EMA_20")
        self.wma = self.I(qi.MovingAverage, self.data.Close, 20, 'wma', overlay=True, name="WMA_20")
        self.atr = self.I(qi.AverageTrueRange, self.data, 14, overlay=False, name="ATR_14")
        self.vol = self.I(qi.MovingAverage, self.data.Volume, 20, 'ema', name="Volume")
        self.dfdt = self.I(qi.Derivative, self.sma, name="DfDt")
        #self.dfdtsma = self.I(qi.MovingAverage, self.dfdt, 20, 'sma', name="DfDtEMA")
        #self.dtdtt = self.I(Derivative, self.dfdt, name="DfDtt")
           
    def next(self):
        price = self.data.Close[-1]
        ema = self.ema[-1]
        time = self.data.index[-1]
        atr = self.atr[-1]
        vol = self.vol[-1]
        dfdt = self.dfdt[-1]
        #dfdtsma = self.dfdtsma[-1]

        # Run if there are no open positions
        if self.position.size == 0:
            if dfdt >= 1:
                print(self.position.size)
                print(f"equity is {self.equity}")
                n_buy = int(round(self.equity/price))-1
                print(f"{n_buy} positions")        
                self.buy(size=n_buy)
                print(f"{time}: {symbol} bought at {price} \n")
                self.highest = price
        
        # Run if there are open positions
        else: 
            if dfdt <= 0:
                print(self.position.size)
                self.position.close()
                profit = self.position.pl
                print(f"{time}: {symbol} sold at {price}")
                print(f"profit is {profit} \n")

class MeanReversion(Strategy):
    def init(self):
        print(f"input data is {self.data.Close}")
        self.sma = self.I(qi.MovingAverage, self.data.Close, 20, 'sma', overlay=True, name="SMA_20")
        self.ema = self.I(qi.MovingAverage, self.data.Close, 20, 'ema', overlay=True, name="EMA_20")
        self.wma = self.I(qi.MovingAverage, self.data.Close, 20, 'wma', overlay=True, name="WMA_20")
        self.atr = self.I(qi.AverageTrueRange, self.data, 14, overlay=False, name="ATR_14")
        self.vol = self.I(qi.MovingAverage, self.data.Volume, 20, 'ema', name="Volume_20")
        self.dfdt = self.I(qi.Derivative, self.data.Close, name="DfDt")
        self.rsi = self.I(qi.RelativeStrengthIndex,self.data.Close, 14,name="RSI_14")
        self.std = self.I(qi.StandardDeviation, self.data.Close, 14, name="STD_20")
        self.commission=0.0025
        print(self.rsi)
        
        #self.cls = self.I(self.data.Close, "name=Close")
        #self.dtdtt = self.I(Derivative, self.dfdt, name="DfDtt")
    def next(self):
        price = self.data.Close[-1]
        ema = self.ema[-1]
        time = self.data.index[-1]
        atr = self.atr[-1]
        rsi = self.rsi[-1]
        std = self.std[-1]
        #if price >= ema*1.02 and self.position.size == 0:

        #optimization variables
        thr_pr_enter = 1
        thr_rsi_enter = 1
        thr_pr_exit = 1
        thr_rsi_exit = 1

        if self.position.size == 0: 
            if price <= ema-std*thr_pr_enter and rsi<30*thr_rsi_enter:
                print(f"Currently holding {self.position.size} positions")
                print(f"cash is {self.equity}")
                n_buy = int(self.equity*0.99//(price*(1+self.commission)))   
                self.highest = price   
                trade = self.buy(size=n_buy, limit=None)
                #trade = self.buy(size=1, limit=None)
                print(f"{time}: \n{n_buy} {symbol} positions bought at {price}")  
                print(f"Total cost of {price*n_buy*(1+self.commission)} \n")

        else: 
            if price >= ema-atr*thr_pr_exit and rsi>30*thr_rsi_exit:
                print(self.position.size)
                self.position.close()
                profit = self.position.pl
                print(f"{time}: {symbol} sold at {price}: Reason: Price reaches EMA")
                print(f"profit is {profit} \n")    
            else:      
                print(f"Current price is {price}")
                if price > self.highest:
                    self.highest = price
                    print(f"New high is {self.highest}")
                if price <= self.highest*0.95:
                    print(self.position.size)
                    self.position.close()
                    profit = self.position.pl
                    print(f"{time}: {symbol} sold at {price} Reason: Trailing Stop Loss")
                    print(f"profit is {profit} \n")

start_date = '2021-06-01'
end_date = '2025-06-01'
sliced_df = df.loc[start_date:end_date]
#print(filtered_df.head())

strategyname = "MomentumStrategy"
foldername = f"F:/TradingBot/Backtests/{strategyname}"
os.makedirs(foldername, exist_ok=True)
filename_equity = f"{foldername}/equity_opt"
filename_sharpe = f"{foldername}/sharpe_opt"
print(foldername)

bt = Backtest(sliced_df,
               MomentumStrategy,
               cash=1000000,
               spread=0,
               commission=0,
               margin=1.0,
               trade_on_close=True,
               hedging=False,
               exclusive_orders=False,
               finalize_trades=False)

stats = bt.run()
bt.plot()
print(stats['_equity_curve'])
print(stats['_trades'])
print(stats)

## Optimize Sharpe ## 
stats, heatmap = bt.optimize(
        return_heatmap=True,
        thr_pr_enter = list(np.arange(0.5,2,0.1)),
        thr_vol_enter = list(np.arange(0.5,2,0.1)),
        thr_pr_exit = list(np.arange(0.5,2,0.1)),
        constraint=lambda p: p.thr_pr_exit <= p.thr_pr_enter,
        maximize='Sharpe Ratio'
        #maximize='Equity Final [$]'
)
heatmap = heatmap.fillna(0)
heatmap = heatmap.sort_values(ascending=False)
#print(heatmap.iloc[:10])
bt.plot(filename=f"{filename_sharpe}.html", open_browser=True)

# Save csv file with parameters
heatmap = heatmap.reset_index(name='value') 
heatmap.to_csv(f"{filename_sharpe}.csv", index=False)

with open(f"{filename_sharpe}.txt", 'w') as f:
    f.write(stats.to_string())

## Optimize Equity ## 
stats, heatmap = bt.optimize(
        return_heatmap=True,
        thr_pr_enter = list(np.arange(0.5,2,0.1)),
        thr_vol_enter = list(np.arange(0.5,2,0.1)),
        thr_pr_exit = list(np.arange(0.5,2,0.1)),
        constraint=lambda p: p.thr_pr_exit <= p.thr_pr_enter,
        #maximize='Sharpe Ratio'
        maximize='Equity Final [$]'
)

heatmap = heatmap.fillna(0)
heatmap = heatmap.sort_values(ascending=False)

bt.plot(filename=f"{filename_equity}.html", open_browser=True)

# Save csv file with parameters
heatmap = heatmap.reset_index(name='value') 
heatmap.to_csv(f"{filename_equity}.csv", index=False)

with open(f"{filename_equity}.txt", 'w') as f:
    f.write(stats.to_string())
