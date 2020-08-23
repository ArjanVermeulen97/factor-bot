#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 21:43:32 2020

@author: Arjan Vermeulen

Perform a sort based on a specified factor
Then long the top, short the bottom
To simulate backtest
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Settings
START_DATE = "01-01-2017"
END_DATE = "31-07-2020"
LEVERAGE = 1
FEE = 0.005
SORT_VAR = 'momentum_1d'
QUANTILE = 0.2
INV_VAR = 1 # Set to -1 to inverse variable

equity = 1
equity_arr = []
df = pandas.read_csv('data.csv')
dates = pd.date_range(START_DATE, END_DATE).to_list()

for index, date in enumerate(dates):
    print(date.strftime("%d-%m-%Y"))
    if index == 0:
        continue
    date_df = df.loc[df['date'] == prevdate]
    return_df = df.loc[df['date'] == date]
    date_df['quantile'] = date_df[SORT_VAR].rank(pct=True)
    longs = date_df.loc[df['quantile'] > 1-QUANTILE, 'asset'].to_list()
    shorts = date_df.loc[df['quantile'] < QUANTILE, 'asset'].to_list()
    if len(longs) == 0 or len(shorts) == 0:
        print("No trades")
        continue
    print("Long:")
    print(longs)
    print("Short:")
    print(shorts)
    long_returns = return_df.loc[return_df['asset'].isin(longs), 'return_1d']
    short_returns = return_df.loc[return_df['asset'].isin(shorts), 'return_1d']
    
    long_return = LEVERAGE * (INV_VAR * np.mean(long_returns.to_numpy()) - FEE)
    short_return = LEVERAGE * (INV_VAR * np.mean(short_returns.to_numpy()) - FEE)
    
    equity = equity * (long_return - short_return)
        
    prevdate = date
    equity_arr.append(equity)
    print(f"Return: {long_return - short_return}")
    print("")
    
plt.plot(equity_arr)
plt.yscale('log')