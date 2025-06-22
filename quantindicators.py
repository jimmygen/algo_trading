## Data series and data frame operations file
import numpy as np
import pandas as pd

def MovingAverage(series, window, weight_type='sma', alpha=None):
    dseries = pd.Series(series)
    if weight_type == 'sma':
        weights = np.ones(window)  # Equal weights (SMA)
    elif weight_type == 'ema':
        alpha = 2 / (window + 1) if alpha is None else alpha
        weights = np.array([(1 - alpha)**i for i in range(window)][::-1])  # Exponential decay
    elif weight_type == 'wma':
        weights = np.arange(1, window + 1, dtype=float)  # Linear weights (WMA)
    else:
        raise ValueError("weight_type must be 'sma', 'ema', or 'wma'.")
    
    # Normalize weights to sum to 1
    weights /= weights.sum()  # Normalize to sum=1
    #normalized_weights = np.true_divide(weights, weights.sum()) 
    
    # Apply convolution
    mva = dseries.rolling(window).apply(lambda x: np.dot(x, weights))
    #print(mva)
    return mva

def AverageTrueRange(datamatrix, window):
    if not isinstance(datamatrix, pd.DataFrame):
        df = datamatrix.df
    else:
        df = datamatrix
    high = df['High'].values
    #print(f" datatype is {type(high)}") 
    low = df['Low'].values
    prev_close = df['Open'].values
    #prev_close = np.roll(df['Close'],1)
    #prev_close[0] = prev_close[1]
    #print(f"values atr are: {high},{low},{prev_close}")
    
    true_range = np.maximum.reduce([
    high - low,
    np.abs(high - prev_close),
    np.abs(low - prev_close)
    ])

    #tr1 = high-low
    #tr2 = abs(high-prev_close)
    #tr3 = abs(low - prev_close)
    #true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = MovingAverage(true_range,window,'ema')
    #print(f"atr is {atr}")
    return atr.values

def Derivative(series):
    dfdt = np.diff(series)
    dfdt = np.concatenate(([dfdt[0]], dfdt)) #Copy first value in beginning to keep equal lengths
    #dfdt = MovingAverage(dfdt, 20, 'ema')
    return dfdt

def RelativeStrengthIndex(series, window):
    dfdt = np.diff(series)
    dfdt = np.concatenate(([dfdt[0]], dfdt)) #Copy first value in beginning to keep equal lengths
    gains = np.where(dfdt > 0, dfdt, 0)
    losses = np.where(dfdt < 0, -dfdt, 0.0)
    
    avg_gain = MovingAverage(gains, window, weight_type='ema')
    avg_loss = MovingAverage(losses, window, weight_type='ema')
    epsilon = 1e-10
    
    rs = avg_gain / (avg_loss+epsilon)
    rsi = 100 - (100/(1+rs))

    return rsi

def StandardDeviation(series, window):
    std = np.empty(len(series))
    std[:window-1] = np.nan
    for i in range(window -1, len(series)):
        std[i] = np.std(series[i-window+1 : i+1], ddof=1)
    return std

def MomentumSignalEntry(datamatrix, window):
    if not isinstance(datamatrix, pd.DataFrame):
        df = datamatrix.df
    else:
        df = datamatrix
    close = df['Close']
    signal = close-MovingAverage(close,window,'ema')-AverageTrueRange(datamatrix,14)*1.5*0.8
    return(signal)

def VolumeSignalEntry(series, window):
    dseries = pd.Series(series)
    signal = dseries-MovingAverage(dseries,window,'ema')*1.5*0.5
    #print(signal)
    return signal

def MomentumSignalExit(datamatrix, window):
    if not isinstance(datamatrix, pd.DataFrame):
        df = datamatrix.df
    else:
        df = datamatrix
    close = df['Close']
    signal = -close+MovingAverage(close,window,'ema')+AverageTrueRange(datamatrix,14)*1.5*0.7
    return(signal)