import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252): # TODO
    """
    Create the Sharpe ratio for the strategy, based on a benchmark of zero.
    Parameters:
    returns: A pandas Series representing period percentage returns
    periods: Daily(252), Hourly(252*6.5)
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def create_drawdowns(pnl):
    """
    Calculate the largest peak-to-through drawdown of the PnL curve as well as 
    the duration of the drawdown. Requires that the pnl_returns is a Pandas Series.
    Parameters:
    pnl: A pandas Series representing the PnL curve
    """
    # set up the Hign Water Mark
    hwm = [0]
    idx = pnl.index
    drawdown = pd.Series(index = idx, dtype='float64')
    duration = pd.Series(index = idx, dtype='float64')
    
    # loop over the index range
    for t in range(1, len(idx)):
        hwm.append(max(hwm[t-1], pnl[t]))
        drawdown[t] = (hwm[t]-pnl[t]) / hwm[t]
        duration[t] = (0 if drawdown[t] == 0 else duration[t-1]+1)
    return drawdown, drawdown.max(), duration.max()

