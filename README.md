# Algorithmic Trading Using Momentum Strategy
## Summary:
**Desciption:** Scripts for automated data fetching, data transformation, strategy development, backtesting, optimization, visualization and trading signal creation**

**Goal of this project:**
- Aid retail investors/traders to make minimal risk but high return trades using leveraging quantitive analysis.
- Provide tools for developing and testing your own strategy

**Built with**: Python, Pandas, Scikit-learn, matplotlib, mplfinance, datetime, pytz, backtesting.py, cctx, dotenv, os

## **Overview:**

**fetch_csv_binance.py:** Create local .csv files of financial data in pandas dataframe style to be used for offline data analysis.
- Uses binance API
- Automatically select most traded cyrptocurreny assets
- Convenient filenaming
- Convenient for pandas dataframe and creating candlestick data (OHLCV)
![Alt text for your image](/images/fetching_result.png "Result of running fetching script")

**main_backtest_CET.py:** Takes .csv input data and strategy('s) and leverages backtesting.py library for backtesting and optimization
- Takes local .csv data and Tranforms UTC data to CET data
- User defined Custom strategy and indicator implementation
- Visual representation of backtest results including Equity Curve, Drawdown visualization, Position visualization, and other custom representations (leveraging backtesting.py)
- Statistical representation including Sharpe Ratio's and other stats (leveraging backtesting.py)
- Full control on parameter optimization and heatmap visualization (leveraging backtesting.py)
![Alt text for your image](/images/backtest_result.png "Backtesting plot")
![Alt text for your image](/images/backtest_stats.png "Backtesting statistics")
![Alt text for your image](/images/optimization_parameters.png "Output df of optimal parameters")

**dashboard.py:** Fetches live data from broker runs indicator/signal operations shows daily dashboard with trading decision
- Flexible broker switching (leveraging cctx library)
- Creates customized dashboard plots using mplfinance library showing processed data
- Can be run daily for buy/hold/sell decision making in trading
![Alt text for your image](/images/20250622_162508_Sell.png "Trading decision dashboard")
  
**fetch_custom_CET.py**: custom python module to fetch live data from given broker and transform from usual UTC timezone to CET timezone.
- Candlestick data is usually in UTC format
- Transform to CET (Europe time) format to schedule and monitor scripts
  
**quantindicators.py**: custom python module for calling custom quantitive indicitors and signals.
- Program own indicators and signals as a single source for the main scripts avoiding errors.


