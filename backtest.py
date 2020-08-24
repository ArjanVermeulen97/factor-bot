#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 21:43:32 2020

@author: Arjan Vermeulen

Perform a sort based on a specified factor
Then long the top, short the bottom, get return, simulate strategy
???
profit!
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Settings
START_DATE = "01-01-2018"
END_DATE = "07-17-2019"
LEVERAGE = 2
FEE = 0.001 * LEVERAGE
SORT_VAR = 'momentum_1d_7d'
NUM_PORTFOLIOS = 5
INV_VAR = 1 # Set to -1 to inverse variable

equity = 100
equity_arr = [100]
drawdown_arr = [1]
high_eq = 1
df = pd.read_csv('data.csv')
dates = pd.date_range(START_DATE, END_DATE).to_list()

for index, date in enumerate(dates):
    print(date.strftime("%d-%m-%Y"))
    if index == 0:
        prevdate = date
        continue
    
    dateString = date.strftime('%Y-%m-%d')
    prevdateString = prevdate.strftime('%Y-%m-%d')
    date_df = df.loc[df['date'] == prevdateString]
    date_df = date_df[date_df.return_1d.notnull()]
    return_df = df.loc[df['date'] == dateString]
    
    date_df['quantile'] = date_df[SORT_VAR].rank(pct=True)
    date_df['portfolio'] = pd.cut(date_df['quantile'],
                                  bins=NUM_PORTFOLIOS,
                                  labels=False)
    longs = date_df.loc[date_df['portfolio'] == NUM_PORTFOLIOS - 1, 'asset'].to_list()
    shorts = date_df.loc[date_df['portfolio'] == 0, 'asset'].to_list()
            
    if len(longs) == 0 or len(shorts) == 0:
        print("No trades")
        equity_arr.append(equity)
        drawdown_arr.append(equity/high_eq)
        prevdate = date
    else:
        print("Long:")
        print(longs)
        print("Short:")
        print(shorts)
        long_returns = return_df.loc[return_df['asset'].isin(longs), 'return_1d']
        short_returns = return_df.loc[return_df['asset'].isin(shorts), 'return_1d']
    
        long_returns = [val-1 for val in long_returns.to_numpy() if pd.notna(val)]
        short_returns = [val-1 for val in short_returns.to_numpy() if pd.notna(val)]
        
        if len(long_returns) == 0:
            long_returns = [0]
        if len(short_returns) == 0:
            short_returns = [0]
        
        long_return = LEVERAGE * (INV_VAR * np.mean(long_returns))
        short_return = LEVERAGE * (INV_VAR * np.mean(short_returns))
        
        
        equity = equity * (long_return - short_return + 1 - FEE)
        
        if equity > high_eq:
            high_eq = equity
        drawdown_arr.append(equity/high_eq)
    
        prevdate = date
        equity_arr.append(equity)
        print(f"Return: {long_return - short_return - FEE}")
        print("")

plt.subplot(211)
plt.plot(equity_arr, label=SORT_VAR)
plt.fill_between(range(len(equity_arr)), 0, equity_arr, alpha=0.5)
plt.xlim((0, len(equity_arr)))
plt.yscale('log')
plt.grid()
plt.legend()
plt.ylabel('Equity [USDT]')
plt.subplot(212)
plt.plot(drawdown_arr, label=SORT_VAR)
plt.fill_between(range(len(drawdown_arr)), 1, drawdown_arr, alpha=0.5)
plt.xlim((0, len(drawdown_arr)))
plt.ylim((0, 1))
plt.grid()
plt.legend()
plt.ylabel('Drawdown [-]')
plt.xlabel('Days')
plt.show()